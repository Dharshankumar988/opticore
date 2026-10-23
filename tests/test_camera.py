"""
Tests for camera capture and bounded buffering.
"""
import pytest
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from camera import CameraService


def test_camera_initialization():
    """Test camera service initialization."""
    camera = CameraService(camera_index=0, width=640, height=480, fps=10)
    
    assert camera.camera_index == 0
    assert camera.width == 640
    assert camera.height == 480
    assert camera.fps == 10
    assert camera.jpeg_quality == 80
    assert camera.running == False
    assert camera.frame_count == 0
    assert camera.dropped_frames == 0


def test_camera_video_file_mode():
    """Test camera with video file input."""
    camera = CameraService(video_file='test.mp4')
    
    assert camera.video_file == 'test.mp4'
    assert camera.camera_index == 0  # Default still


def test_frame_queue_bounded():
    """Test that frame queue is bounded and prefers newest frames."""
    camera = CameraService()
    
    # Queue should have maxsize 2
    assert camera.frame_queue.maxsize == 2
    
    # Fill queue
    camera.frame_queue.put_nowait(b'frame1')
    camera.frame_queue.put_nowait(b'frame2')
    
    # Third frame should fail (queue full)
    with pytest.raises(Exception):  # queue.Full
        camera.frame_queue.put_nowait(b'frame3')


def test_get_stats():
    """Test camera statistics."""
    camera = CameraService()
    stats = camera.get_stats()
    
    assert 'running' in stats
    assert 'frame_count' in stats
    assert 'dropped_frames' in stats
    assert 'actual_fps' in stats
    assert 'target_fps' in stats
    assert 'camera_index' in stats
    assert 'resolution' in stats


def test_camera_discovery():
    """Test camera discovery (may not find cameras in test environment)."""
    cameras = CameraService.discover_cameras(max_index=3)
    
    # Should return a list
    assert isinstance(cameras, list)
    
    # Each camera should be a tuple
    for cam in cameras:
        assert isinstance(cam, tuple)
        assert len(cam) == 2
        assert isinstance(cam[0], int)
        assert isinstance(cam[1], str)


def test_get_frame_when_empty():
    """Test getting frame when queue is empty."""
    camera = CameraService()
    frame = camera.get_frame()
    
    # Should return None when empty
    assert frame is None
