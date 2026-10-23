"""
WebSocket connections, streaming and result handling for OptiCore Device Client.
"""
import asyncio
import websockets
import json
import time
import logging
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of inference events from the server."""
    DETECTION = "detection"
    OCR = "ocr"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class Detection:
    """Object detection result."""
    class_name: str
    confidence: float
    bbox: list[float]  # [x1, y1, x2, y2]
    track_id: Optional[int] = None


@dataclass
class OCRResult:
    """OCR text result."""
    text: str
    confidence: float
    bbox: Optional[list[float]] = None


@dataclass
class InferenceEvent:
    """Inference event from the server."""
    event_type: EventType
    timestamp: float
    detections: list[Detection]
    ocr_results: list[OCRResult]
    raw_data: Dict[str, Any]


class ServerClient:
    """Manages WebSocket connections to the OptiCore server."""
    
    def __init__(self, server_url: str, client_id: str, 
                 max_reconnect_delay: int = 30, initial_reconnect_delay: int = 1,
                 timeout: int = 10):
        self.server_url = server_url
        self.client_id = client_id
        self.max_reconnect_delay = max_reconnect_delay
        self.initial_reconnect_delay = initial_reconnect_delay
        self.timeout = timeout
        
        self.video_ws: Optional[websockets.WebSocketClientProtocol] = None
        self.events_ws: Optional[websockets.WebSocketClientProtocol] = None
        
        self.running = False
        self.video_task: Optional[asyncio.Task] = None
        self.events_task: Optional[asyncio.Task] = None
        
        self.event_callback: Optional[Callable[[InferenceEvent], None]] = None
        self.status_callback: Optional[Callable[[str, str], None]] = None
        
        self.frames_sent = 0
        self.connection_errors = 0
        self.last_heartbeat = 0
        self.connected = False
        
    def set_event_callback(self, callback: Callable[[InferenceEvent], None]):
        """Set callback for inference events."""
        self.event_callback = callback
    
    def set_status_callback(self, callback: Callable[[str, str], None]):
        """Set callback for connection status updates (component, status)."""
        self.status_callback = callback
    
    async def check_health(self) -> bool:
        """Check server health via GET /health endpoint."""
        try:
            # Convert ws:// to http:// or wss:// to https://
            http_url = self.server_url.replace('ws://', 'http://').replace('wss://', 'https://')
            health_url = f"{http_url}/health"
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(health_url, timeout=self.timeout) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def start(self):
        """Start WebSocket connections."""
        if self.running:
            return
        
        self.running = True
        
        # Start event listener first
        self.events_task = asyncio.create_task(self._events_loop())
        
        # Wait a moment for events connection
        await asyncio.sleep(0.5)
        
        # Start video sender
        self.video_task = asyncio.create_task(self._video_loop())
    
    async def stop(self):
        """Stop WebSocket connections."""
        self.running = False
        
        if self.video_task:
            self.video_task.cancel()
            try:
                await self.video_task
            except asyncio.CancelledError:
                pass
        
        if self.events_task:
            self.events_task.cancel()
            try:
                await self.events_task
            except asyncio.CancelledError:
                pass
        
        if self.video_ws:
            await self.video_ws.close()
        if self.events_ws:
            await self.events_ws.close()
        
        self.connected = False
        self._notify_status('server', 'disconnected')
    
    def send_frame(self, frame_bytes: bytes):
        """Send a frame to the video WebSocket (non-blocking)."""
        if self.video_ws and self.connected:
            asyncio.create_task(self._send_frame_async(frame_bytes))
    
    async def _send_frame_async(self, frame_bytes: bytes):
        """Async frame sending."""
        try:
            if self.video_ws and self.connected:
                await self.video_ws.send(frame_bytes)
                self.frames_sent += 1
        except Exception as e:
            logger.error(f"Failed to send frame: {e}")
            self.connection_errors += 1
    
    async def _connect_with_backoff(self, endpoint: str) -> Optional[websockets.WebSocketClientProtocol]:
        """Connect to WebSocket endpoint with exponential backoff."""
        url = f"{self.server_url}{endpoint}"
        delay = self.initial_reconnect_delay
        
        while self.running:
            try:
                ws = await asyncio.wait_for(
                    websockets.connect(url, extra_headers={'X-Client-ID': self.client_id}),
                    timeout=self.timeout
                )
                logger.info(f"Connected to {endpoint}")
                return ws
            except Exception as e:
                logger.warning(f"Failed to connect to {endpoint}: {e}, retrying in {delay}s")
                await asyncio.sleep(delay)
                delay = min(delay * 2, self.max_reconnect_delay)
        
        return None
    
    async def _video_loop(self):
        """Video streaming loop with reconnection."""
        while self.running:
            try:
                self.video_ws = await self._connect_with_backoff('/ws/video')
                if not self.video_ws:
                    continue
                
                self.connected = True
                self._notify_status('video', 'connected')
                
                # Keep connection alive
                while self.running:
                    try:
                        await asyncio.sleep(1)
                        # Optional: send keepalive if needed
                    except Exception as e:
                        logger.error(f"Video connection error: {e}")
                        break
                
            except Exception as e:
                logger.error(f"Video loop error: {e}")
                self.connection_errors += 1
            finally:
                if self.video_ws:
                    await self.video_ws.close()
                self.connected = False
                self._notify_status('video', 'disconnected')
                await asyncio.sleep(1)
    
    async def _events_loop(self):
        """Events receiving loop with reconnection."""
        while self.running:
            try:
                self.events_ws = await self._connect_with_backoff('/ws/events')
                if not self.events_ws:
                    continue
                
                self._notify_status('events', 'connected')
                
                # Receive events
                while self.running:
                    try:
                        message = await asyncio.wait_for(self.events_ws.recv(), timeout=30)
                        await self._handle_message(message)
                    except asyncio.TimeoutError:
                        # Send ping to keep connection alive
                        try:
                            await self.events_ws.ping()
                        except:
                            break
                    except Exception as e:
                        logger.error(f"Events receive error: {e}")
                        break
                
            except Exception as e:
                logger.error(f"Events loop error: {e}")
            finally:
                if self.events_ws:
                    await self.events_ws.close()
                self._notify_status('events', 'disconnected')
                await asyncio.sleep(1)
    
    async def _handle_message(self, message: str):
        """Parse and handle incoming event message."""
        try:
            data = json.loads(message)
            event = self._parse_event(data)
            
            if event:
                self.last_heartbeat = time.time()
                if self.event_callback:
                    # Run callback in thread pool to avoid blocking
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.event_callback, event
                    )
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def _parse_event(self, data: Dict[str, Any]) -> Optional[InferenceEvent]:
        """Parse server event into InferenceEvent."""
        try:
            event_type_str = data.get('type', 'unknown')
            event_type = EventType.UNKNOWN
            
            if event_type_str == 'detection':
                event_type = EventType.DETECTION
            elif event_type_str == 'ocr':
                event_type = EventType.OCR
            elif event_type_str == 'heartbeat':
                event_type = EventType.HEARTBEAT
            elif event_type_str == 'error':
                event_type = EventType.ERROR
            
            # Parse detections
            detections = []
            if 'detections' in data:
                for det in data['detections']:
                    detections.append(Detection(
                        class_name=det.get('class_name', 'unknown'),
                        confidence=det.get('confidence', 0.0),
                        bbox=det.get('bbox', []),
                        track_id=det.get('track_id')
                    ))
            
            # Parse OCR results
            ocr_results = []
            if 'ocr_results' in data:
                for ocr in data['ocr_results']:
                    ocr_results.append(OCRResult(
                        text=ocr.get('text', ''),
                        confidence=ocr.get('confidence', 0.0),
                        bbox=ocr.get('bbox')
                    ))
            
            return InferenceEvent(
                event_type=event_type,
                timestamp=data.get('timestamp', time.time()),
                detections=detections,
                ocr_results=ocr_results,
                raw_data=data
            )
        
        except Exception as e:
            logger.error(f"Error parsing event: {e}")
            return None
    
    def _notify_status(self, component: str, status: str):
        """Notify status callback."""
        if self.status_callback:
            try:
                self.status_callback(component, status)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
    
    def get_stats(self) -> dict:
        """Get connection statistics."""
        return {
            'connected': self.connected,
            'frames_sent': self.frames_sent,
            'connection_errors': self.connection_errors,
            'last_heartbeat': self.last_heartbeat,
            'server_url': self.server_url
        }
