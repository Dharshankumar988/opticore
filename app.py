"""
OptiCore Device Client - Main application entry point.
"""
import asyncio
import logging
import signal
import sys
import os
from pathlib import Path
from typing import Optional
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import threading
import webbrowser

from config import config
from camera import CameraService
from server_client import ServerClient, InferenceEvent
from tts_service import TTSService
from bluetooth_service import BluetoothService
from alert_manager import AlertManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OptiCoreApp:
    """Main application class."""
    
    def __init__(self):
        self.config = config
        
        # Validate configuration
        errors = self.config.validate()
        if errors:
            logger.error("Configuration errors:")
            for error in errors:
                logger.error(f"  - {error}")
            logger.warning("Application will start but may not function correctly")
        
        # Initialize services
        self.camera = CameraService(
            camera_index=self.config.CAMERA_INDEX,
            width=self.config.CAMERA_WIDTH,
            height=self.config.CAMERA_HEIGHT,
            fps=self.config.STREAM_FPS,
            jpeg_quality=self.config.JPEG_QUALITY,
            video_file=self.config.VIDEO_FILE_PATH
        )
        
        self.server_client = ServerClient(
            server_url=self.config.OPTICORE_SERVER_URL,
            client_id=self.config.OPTICORE_CLIENT_ID,
            max_reconnect_delay=self.config.WS_MAX_RECONNECT_DELAY,
            initial_reconnect_delay=self.config.WS_INITIAL_RECONNECT_DELAY,
            timeout=self.config.WS_TIMEOUT
        )
        
        self.tts = TTSService(
            enabled=self.config.TTS_ENABLED,
            rate=self.config.TTS_RATE,
            volume=self.config.TTS_VOLUME
        )
        
        self.bluetooth = BluetoothService()
        self.alert_manager = AlertManager(
            cooldown_seconds=self.config.ALERT_COOLDOWN_SECONDS,
            verbosity=self.config.ALERT_VERBOSITY
        )
        
        # State
        self.streaming = False
        self.latest_event: Optional[InferenceEvent] = None
        self.async_loop: Optional[asyncio.AbstractEventLoop] = None
        self.async_thread: Optional[threading.Thread] = None
        
        # Setup callbacks
        self.server_client.set_event_callback(self._handle_inference_event)
        self.server_client.set_status_callback(self._handle_connection_status)
        
        # Flask app
        self.flask_app = Flask(__name__, 
                              template_folder=str(Path(__file__).parent / 'web'),
                              static_folder=str(Path(__file__).parent / 'web'))
        CORS(self.flask_app)
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.flask_app.route('/')
        def index():
            return render_template('index.html')
        
        @self.flask_app.route('/api/status')
        def get_status():
            return jsonify(self._get_status())
        
        @self.flask_app.route('/api/cameras')
        def get_cameras():
            cameras = CameraService.discover_cameras()
            return jsonify({'cameras': cameras})
        
        @self.flask_app.route('/api/start', methods=['POST'])
        def start_streaming():
            data = request.json or {}
            camera_index = data.get('camera_index', self.config.CAMERA_INDEX)
            
            if self.streaming:
                return jsonify({'status': 'already_streaming'})
            
            self.camera.camera_index = camera_index
            if self.camera.start():
                self.streaming = True
                # Start server client in async loop
                if self.async_loop:
                    asyncio.run_coroutine_threadsafe(
                        self.server_client.start(),
                        self.async_loop
                    )
                return jsonify({'status': 'started'})
            else:
                return jsonify({'status': 'failed', 'error': 'Camera not available'})
        
        @self.flask_app.route('/api/stop', methods=['POST'])
        def stop_streaming():
            if not self.streaming:
                return jsonify({'status': 'not_streaming'})
            
            self.streaming = False
            self.camera.stop()
            
            if self.async_loop:
                asyncio.run_coroutine_threadsafe(
                    self.server_client.stop(),
                    self.async_loop
                )
            
            return jsonify({'status': 'stopped'})
        
        @self.flask_app.route('/api/config', methods=['GET', 'POST'])
        def handle_config():
            if request.method == 'POST':
                data = request.json
                # Update configuration
                if 'camera_index' in data:
                    self.config.CAMERA_INDEX = int(data['camera_index'])
                if 'server_url' in data:
                    self.config.OPTICORE_SERVER_URL = data['server_url']
                if 'tts_enabled' in data:
                    self.config.TTS_ENABLED = data['tts_enabled'] == 'true'
                if 'tts_rate' in data:
                    self.config.TTS_RATE = int(data['tts_rate'])
                if 'tts_volume' in data:
                    self.config.TTS_VOLUME = float(data['tts_volume'])
                if 'alert_verbosity' in data:
                    self.config.ALERT_VERBOSITY = data['alert_verbosity']
                
                return jsonify({'status': 'updated'})
            else:
                return jsonify({
                    'server_url': self.config.OPTICORE_SERVER_URL,
                    'camera_index': self.config.CAMERA_INDEX,
                    'tts_enabled': self.config.TTS_ENABLED,
                    'tts_rate': self.config.TTS_RATE,
                    'tts_volume': self.config.TTS_VOLUME,
                    'alert_verbosity': self.config.ALERT_VERBOSITY
                })
        
        @self.flask_app.route('/api/tts/test', methods=['POST'])
        def test_tts():
            self.tts.test_speech()
            return jsonify({'status': 'testing'})
        
        @self.flask_app.route('/api/tts/mute', methods=['POST'])
        def mute_tts():
            self.tts.stop_speech()
            return jsonify({'status': 'muted'})
        
        @self.flask_app.route('/api/audio-devices')
        def get_audio_devices():
            devices = self.bluetooth.discover_audio_devices()
            return jsonify({'devices': devices})
        
        @self.flask_app.route('/api/health-check', methods=['POST'])
        async def health_check():
            if self.async_loop:
                healthy = await self.server_client.check_health()
                return jsonify({'healthy': healthy})
            return jsonify({'healthy': False, 'error': 'Async loop not ready'})
    
    def _get_status(self) -> dict:
        """Get current application status."""
        camera_stats = self.camera.get_stats()
        server_stats = self.server_client.get_stats()
        tts_stats = self.tts.get_stats()
        bluetooth_status = self.bluetooth.get_status()
        alert_stats = self.alert_manager.get_stats()
        
        latest_result = None
        if self.latest_event:
            latest_result = {
                'timestamp': self.latest_event.timestamp,
                'detections': [
                    {
                        'class_name': d.class_name,
                        'confidence': d.confidence,
                        'track_id': d.track_id
                    }
                    for d in self.latest_event.detections
                ],
                'ocr_results': [
                    {'text': o.text, 'confidence': o.confidence}
                    for o in self.latest_event.ocr_results
                ]
            }
        
        return {
            'streaming': self.streaming,
            'camera': camera_stats,
            'server': server_stats,
            'tts': tts_stats,
            'bluetooth': bluetooth_status,
            'alerts': alert_stats,
            'latest_result': latest_result
        }
    
    def _handle_inference_event(self, event: InferenceEvent):
        """Handle inference event from server."""
        self.latest_event = event
        
        # Process detections for alerts
        for detection in event.detections:
            message = self.alert_manager.add_detection_alert(
                detection.class_name,
                detection.confidence,
                detection.track_id
            )
            if message:
                self.tts.speak(message)
        
        # Process OCR for alerts
        for ocr in event.ocr_results:
            message = self.alert_manager.add_ocr_alert(ocr.text, ocr.confidence)
            if message:
                self.tts.speak(message)
    
    def _handle_connection_status(self, component: str, status: str):
        """Handle connection status updates."""
        logger.info(f"Connection status: {component} -> {status}")
    
    def _async_loop_runner(self):
        """Run async event loop in background thread."""
        self.async_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.async_loop)
        self.async_loop.run_forever()
    
    def start(self):
        """Start the application."""
        logger.info("Starting OptiCore Device Client...")
        
        # Start TTS
        self.tts.start()
        
        # Start async loop
        self.async_thread = threading.Thread(target=self._async_loop_runner, daemon=True)
        self.async_thread.start()
        
        # Wait for async loop to be ready
        import time
        time.sleep(0.5)
        
        # Start Flask
        url = f"http://{self.config.HOST}:{self.config.PORT}"
        logger.info(f"Dashboard available at {url}")
        
        # Open browser
        try:
            webbrowser.open(url)
        except:
            pass
        
        self.flask_app.run(
            host=self.config.HOST,
            port=self.config.PORT,
            debug=False,
            use_reloader=False
        )
    
    def shutdown(self):
        """Cleanup on shutdown."""
        logger.info("Shutting down...")
        
        self.streaming = False
        self.camera.stop()
        
        if self.async_loop:
            asyncio.run_coroutine_threadsafe(
                self.server_client.stop(),
                self.async_loop
            )
        
        self.tts.stop()
        
        if self.async_loop:
            self.async_loop.call_soon_threadsafe(self.async_loop.stop)


def main():
    """Main entry point."""
    app = OptiCoreApp()
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        app.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        app.start()
    except KeyboardInterrupt:
        app.shutdown()
    except Exception as e:
        logger.error(f"Application error: {e}")
        app.shutdown()
        sys.exit(1)


if __name__ == '__main__':
    main()
