"""
Tests for WebSocket event parsing and protocol handling.
"""
import pytest
import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server_client import ServerClient, InferenceEvent, Detection, OCRResult, EventType


def test_server_client_initialization():
    """Test server client initialization."""
    client = ServerClient(
        server_url='ws://localhost:8080',
        client_id='test-client'
    )
    
    assert client.server_url == 'ws://localhost:8080'
    assert client.client_id == 'test-client'
    assert client.running == False
    assert client.connected == False
    assert client.frames_sent == 0


def test_parse_detection_event():
    """Test parsing detection event from server."""
    client = ServerClient('ws://localhost:8080', 'test-client')
    
    data = {
        'type': 'detection',
        'timestamp': 1234567890.123,
        'detections': [
            {
                'class_name': 'person',
                'confidence': 0.95,
                'bbox': [10, 20, 100, 200],
                'track_id': 1
            }
        ]
    }
    
    event = client._parse_event(data)
    
    assert event is not None
    assert event.event_type == EventType.DETECTION
    assert len(event.detections) == 1
    assert event.detections[0].class_name == 'person'
    assert event.detections[0].confidence == 0.95
    assert event.detections[0].track_id == 1


def test_parse_ocr_event():
    """Test parsing OCR event from server."""
    client = ServerClient('ws://localhost:8080', 'test-client')
    
    data = {
        'type': 'ocr',
        'timestamp': 1234567890.123,
        'ocr_results': [
            {
                'text': 'Hello World',
                'confidence': 0.85,
                'bbox': [10, 20, 100, 50]
            }
        ]
    }
    
    event = client._parse_event(data)
    
    assert event is not None
    assert event.event_type == EventType.OCR
    assert len(event.ocr_results) == 1
    assert event.ocr_results[0].text == 'Hello World'
    assert event.ocr_results[0].confidence == 0.85


def test_parse_heartbeat_event():
    """Test parsing heartbeat event."""
    client = ServerClient('ws://localhost:8080', 'test-client')
    
    data = {
        'type': 'heartbeat',
        'timestamp': 1234567890.123
    }
    
    event = client._parse_event(data)
    
    assert event is not None
    assert event.event_type == EventType.HEARTBEAT


def test_parse_unknown_event():
    """Test parsing unknown event type."""
    client = ServerClient('ws://localhost:8080', 'test-client')
    
    data = {
        'type': 'unknown_type',
        'timestamp': 1234567890.123
    }
    
    event = client._parse_event(data)
    
    assert event is not None
    assert event.event_type == EventType.UNKNOWN


def test_parse_invalid_json():
    """Test handling of invalid JSON."""
    client = ServerClient('ws://localhost:8080', 'test-client')
    
    # Should not crash on invalid data
    event = client._parse_event({})
    assert event is not None  # Still returns event with defaults


def test_parse_missing_fields():
    """Test parsing event with missing fields."""
    client = ServerClient('ws://localhost:8080', 'test-client')
    
    data = {
        'type': 'detection'
        # Missing timestamp and detections
    }
    
    event = client._parse_event(data)
    
    assert event is not None
    assert event.event_type == EventType.DETECTION
    assert len(event.detections) == 0  # Empty list


def test_get_stats():
    """Test getting connection statistics."""
    client = ServerClient('ws://localhost:8080', 'test-client')
    stats = client.get_stats()
    
    assert 'connected' in stats
    assert 'frames_sent' in stats
    assert 'connection_errors' in stats
    assert 'last_heartbeat' in stats
    assert 'server_url' in stats


def test_detection_dataclass():
    """Test Detection dataclass."""
    detection = Detection(
        class_name='person',
        confidence=0.95,
        bbox=[10, 20, 100, 200],
        track_id=1
    )
    
    assert detection.class_name == 'person'
    assert detection.confidence == 0.95
    assert detection.bbox == [10, 20, 100, 200]
    assert detection.track_id == 1


def test_ocr_result_dataclass():
    """Test OCRResult dataclass."""
    ocr = OCRResult(
        text='Test',
        confidence=0.85,
        bbox=[10, 20, 100, 50]
    )
    
    assert ocr.text == 'Test'
    assert ocr.confidence == 0.85
    assert ocr.bbox == [10, 20, 100, 50]


def test_multiple_detections():
    """Test parsing multiple detections."""
    client = ServerClient('ws://localhost:8080', 'test-client')
    
    data = {
        'type': 'detection',
        'timestamp': 1234567890.123,
        'detections': [
            {'class_name': 'person', 'confidence': 0.95, 'bbox': [10, 20, 100, 200], 'track_id': 1},
            {'class_name': 'car', 'confidence': 0.88, 'bbox': [200, 20, 300, 200], 'track_id': 2},
            {'class_name': 'dog', 'confidence': 0.75, 'bbox': [50, 150, 150, 250]}
        ]
    }
    
    event = client._parse_event(data)
    
    assert event is not None
    assert len(event.detections) == 3
    assert event.detections[0].class_name == 'person'
    assert event.detections[1].class_name == 'car'
    assert event.detections[2].class_name == 'dog'
    assert event.detections[2].track_id is None  # No track ID for third detection


def test_sanitization_required():
    """Test that OCR text should be sanitized (placeholder for future implementation)."""
    # This test documents the requirement
    # Actual sanitization is done in alert_manager
    client = ServerClient('ws://localhost:8080', 'test-client')
    
    data = {
        'type': 'ocr',
        'timestamp': 1234567890.123,
        'ocr_results': [
            {
                'text': '<script>alert("xss")</script>',
                'confidence': 0.85
            }
        ]
    }
    
    event = client._parse_event(data)
    
    # Event is parsed, but sanitization should happen before display/speech
    assert event is not None
    assert event.ocr_results[0].text == '<script>alert("xss")</script>'
    # Sanitization is responsibility of alert_manager
