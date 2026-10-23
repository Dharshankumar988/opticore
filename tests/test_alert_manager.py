"""
Tests for alert manager - deduplication and prioritization.
"""
import time
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alert_manager import AlertManager


def test_alert_manager_initialization():
    """Test alert manager initialization."""
    manager = AlertManager()
    
    assert manager.cooldown_seconds == 5
    assert manager.verbosity == 'normal'
    assert len(manager.alert_history) == 0
    assert len(manager.track_history) == 0


def test_detection_alert_deduplication():
    """Test that duplicate detection alerts are deduplicated."""
    manager = AlertManager(cooldown_seconds=1)
    
    # First alert should be spoken
    message1 = manager.add_detection_alert('person', 0.9)
    assert message1 is not None
    
    # Immediate duplicate should not be spoken
    message2 = manager.add_detection_alert('person', 0.9)
    assert message2 is None
    
    # Wait for cooldown
    time.sleep(1.1)
    
    # After cooldown, should be spoken again
    message3 = manager.add_detection_alert('person', 0.9)
    assert message3 is not None


def test_track_id_deduplication():
    """Test that alerts with same track ID are deduplicated."""
    manager = AlertManager(cooldown_seconds=1)
    
    # First alert with track ID should be spoken
    message1 = manager.add_detection_alert('person', 0.9, track_id=1)
    assert message1 is not None
    
    # Same track ID should not be spoken immediately
    message2 = manager.add_detection_alert('person', 0.9, track_id=1)
    assert message2 is None
    
    # Different track ID should be spoken
    message3 = manager.add_detection_alert('person', 0.9, track_id=2)
    assert message3 is not None


def test_ocr_alert_deduplication():
    """Test that OCR alerts are deduplicated."""
    manager = AlertManager(cooldown_seconds=1)
    
    # First OCR alert should be spoken
    message1 = manager.add_ocr_alert('Hello World', 0.9)
    assert message1 is not None
    assert 'It says' in message1
    
    # Immediate duplicate should not be spoken
    message2 = manager.add_ocr_alert('Hello World', 0.9)
    assert message2 is None


def test_ocr_text_sanitization():
    """Test that OCR text is sanitized."""
    manager = AlertManager()
    
    # Test with special characters
    message = manager.add_ocr_alert('Test\x00\x01\x02Text', 0.9)
    if message:
        # Should not contain control characters
        assert '\x00' not in message
        assert '\x01' not in message


def test_proximity_alert_priority():
    """Test that proximity alerts are high priority."""
    manager = AlertManager()
    
    message = manager.add_proximity_alert('Obstacle ahead')
    assert message is not None
    assert 'Obstacle ahead' in message


def test_verbosity_levels():
    """Test different verbosity levels."""
    # Minimal verbosity
    manager_minimal = AlertManager(verbosity='minimal')
    message = manager_minimal.add_detection_alert('person', 0.9)
    assert message is None  # Minimal should suppress normal detections
    
    # Normal verbosity
    manager_normal = AlertManager(verbosity='normal')
    message = manager_normal.add_detection_alert('person', 0.9)
    assert message is not None
    
    # Verbose verbosity
    manager_verbose = AlertManager(verbosity='verbose')
    message = manager_verbose.add_detection_alert('person', 0.9)
    assert message is not None


def test_clear_history():
    """Test clearing alert history."""
    manager = AlertManager(cooldown_seconds=10)
    
    # Add an alert
    manager.add_detection_alert('person', 0.9)
    assert len(manager.alert_history) > 0
    
    # Clear history
    manager.clear_history()
    assert len(manager.alert_history) == 0
    assert len(manager.track_history) == 0


def test_detection_classification():
    """Test detection classification into alert types."""
    manager = AlertManager()
    
    # Obstacle classification
    assert manager._classify_detection('obstacle') == 'obstacle'
    assert manager._classify_detection('barrier') == 'obstacle'
    
    # Person classification
    assert manager._classify_detection('person') == 'person'
    assert manager._classify_detection('human') == 'person'
    
    # Vehicle classification
    assert manager._classify_detection('car') == 'vehicle'
    assert manager._classify_detection('truck') == 'vehicle'
    
    # Default classification
    assert manager._classify_detection('unknown') == 'info'


def test_detection_message_formatting():
    """Test detection message formatting based on confidence."""
    manager = AlertManager()
    
    # High confidence
    msg_high = manager._format_detection_message('person', 0.9)
    assert msg_high == 'person'
    
    # Medium confidence
    msg_med = manager._format_detection_message('person', 0.6)
    assert 'Possible' in msg_med
    
    # Low confidence
    msg_low = manager._format_detection_message('person', 0.3)
    assert 'Uncertain' in msg_low
