"""
Camera discovery, capture and frame encoding for OptiCore Device Client.
"""
import cv2
import threading
import queue
import time
from typing import Optional, List, Tuple
import numpy as np


class CameraService:
    """Manages camera discovery, capture and frame encoding."""
    
    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480, 
                 fps: int = 10, jpeg_quality: int = 80, video_file: Optional[str] = None):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self.jpeg_quality = jpeg_quality
        self.video_file = video_file
        
        self.cap: Optional[cv2.VideoCapture] = None
        self.running = False
        self.capture_thread: Optional[threading.Thread] = None
        self.frame_queue: queue.Queue = queue.Queue(maxsize=2)  # Bounded buffer
        self.frame_count = 0
        self.dropped_frames = 0
        self.last_frame_time = 0
        self.actual_fps = 0
        self.last_error: Optional[str] = None
        self.consecutive_errors = 0
        self.frame_callback = None  # Callback to send frames to server
        
    @staticmethod
    def discover_cameras(max_index: int = 10) -> List[Tuple[int, str]]:
        """Discover available camera devices."""
        available = []
        for i in range(max_index):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # Try to get camera name if available
                backend_name = cap.getBackendName()
                available.append((i, f"Camera {i} ({backend_name})"))
                cap.release()
        return available
    
    def start(self) -> bool:
        """Start camera capture."""
        if self.running:
            return True
        
        self.last_error = None
        self.consecutive_errors = 0
        
        if self.video_file:
            self.cap = cv2.VideoCapture(self.video_file)
        else:
            self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap or not self.cap.isOpened():
            self.last_error = f"Failed to open camera {self.camera_index}"
            return False
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        # Verify camera is actually capturing by reading a test frame
        ret, test_frame = self.cap.read()
        if not ret or test_frame is None:
            self.cap.release()
            self.cap = None
            self.last_error = "Camera opened but failed to read test frame"
            return False
        
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        return True
    
    def stop(self):
        """Stop camera capture."""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def _capture_loop(self):
        """Continuous camera capture loop."""
        frame_interval = 1.0 / self.fps
        last_capture_time = time.time()
        
        while self.running:
            current_time = time.time()
            elapsed = current_time - last_capture_time
            
            if elapsed < frame_interval:
                time.sleep(frame_interval - elapsed)
                continue
            
            ret, frame = self.cap.read()
            if not ret:
                self.consecutive_errors += 1
                if self.consecutive_errors > 10:
                    self.last_error = f"Failed to read frame after {self.consecutive_errors} attempts"
                    logger.error(self.last_error)
                time.sleep(0.1)
                continue
            
            # Reset error counter on successful read
            self.consecutive_errors = 0
            
            # Calculate actual FPS
            self.last_frame_time = current_time
            if elapsed > 0:
                self.actual_fps = 1.0 / elapsed
            
            # Encode to JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
            success, encoded = cv2.imencode('.jpg', frame, encode_param)
            
            if success:
                self.frame_count += 1
                frame_bytes = encoded.tobytes()
                
                # Prefer newest frame - drop if queue is full
                try:
                    self.frame_queue.put_nowait(frame_bytes)
                except queue.Full:
                    self.dropped_frames += 1
                    # Remove oldest and add newest
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame_bytes)
                    except queue.Empty:
                        pass
                
                # Send frame to server via callback
                if self.frame_callback:
                    try:
                        self.frame_callback(frame_bytes)
                    except Exception as e:
                        logger.error(f"Frame callback error: {e}")
            
            last_capture_time = current_time
    
    def get_frame(self) -> Optional[bytes]:
        """Get the latest encoded frame from the buffer."""
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Get the latest raw frame for preview (not encoded)."""
        if not self.cap or not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        return frame if ret else None
    
    def get_stats(self) -> dict:
        """Get camera statistics."""
        return {
            'running': self.running,
            'frame_count': self.frame_count,
            'dropped_frames': self.dropped_frames,
            'actual_fps': self.actual_fps,
            'target_fps': self.fps,
            'camera_index': self.camera_index,
            'resolution': f"{self.width}x{self.height}",
            'last_error': self.last_error,
            'consecutive_errors': self.consecutive_errors
        }
    
    def set_frame_callback(self, callback):
        """Set callback function to receive frames (for server streaming)."""
        self.frame_callback = callback
