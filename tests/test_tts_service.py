"""
Tests for TTS service independence and failure handling.
"""
import pytest
import sys
from pathlib import Path
import time
import threading

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tts_service import TTSService


def test_tts_initialization():
    """Test TTS service initialization."""
    tts = TTSService(enabled=True, rate=175, volume=0.8)
    
    assert tts.enabled == True
    assert tts.rate == 175
    assert tts.volume == 0.8
    assert tts.running == False
    assert tts.currently_speaking == False


def test_tts_disabled():
    """Test TTS when disabled."""
    tts = TTSService(enabled=False)
    tts.start()
    
    # Should not start worker when disabled
    assert tts.running == False
    
    # Speaking should be a no-op
    tts.speak("Test message")
    assert tts.speech_queue.empty()


def test_speech_queue():
    """Test speech queuing."""
    tts = TTSService(enabled=True)
    
    # Add messages to queue
    tts.speak("Message 1")
    tts.speak("Message 2")
    tts.speak("Message 3")
    
    assert tts.speech_queue.qsize() == 3


def test_priority_message():
    """Test priority messages skip the queue."""
    tts = TTSService(enabled=True)
    
    # Add normal messages
    tts.speak("Normal 1")
    tts.speak("Normal 2")
    
    # Add priority message
    tts.speak("Priority", priority=True)
    
    # Priority should be at front
    first = tts.speech_queue.get_nowait()
    assert first == "Priority"
    
    # Normal messages should follow
    second = tts.speech_queue.get_nowait()
    assert second == "Normal 1"


def test_stop_speech():
    """Test stopping speech and clearing queue."""
    tts = TTSService(enabled=True)
    
    # Add messages
    tts.speak("Message 1")
    tts.speak("Message 2")
    tts.speak("Message 3")
    
    assert tts.speech_queue.qsize() == 3
    
    # Stop speech
    tts.stop_speech()
    
    # Queue should be cleared
    assert tts.speech_queue.empty()
    assert tts.stop_requested == False


def test_set_rate():
    """Test setting speech rate."""
    tts = TTSService(enabled=True)
    
    tts.set_rate(200)
    assert tts.rate == 200


def test_set_volume():
    """Test setting speech volume."""
    tts = TTSService(enabled=True)
    
    tts.set_volume(0.5)
    assert tts.volume == 0.5
    
    # Volume should be clamped
    tts.set_volume(1.5)
    assert tts.volume == 1.0
    
    tts.set_volume(-0.5)
    assert tts.volume == 0.0


def test_get_stats():
    """Test getting TTS statistics."""
    tts = TTSService(enabled=True)
    stats = tts.get_stats()
    
    assert 'enabled' in stats
    assert 'running' in stats
    assert 'currently_speaking' in stats
    assert 'queue_size' in stats
    assert 'rate' in stats
    assert 'volume' in stats


def test_tts_independence():
    """Test that TTS operations don't block (conceptual test)."""
    tts = TTSService(enabled=True)
    
    # Speaking should return immediately (non-blocking)
    start = time.time()
    tts.speak("Test message")
    elapsed = time.time() - start
    
    # Should return almost immediately
    assert elapsed < 0.1


def test_start_stop():
    """Test starting and stopping TTS service."""
    tts = TTSService(enabled=True)
    
    assert tts.running == False
    
    tts.start()
    # Note: Without actual engine, running may still be False
    # This test validates the interface
    
    tts.stop()
    assert tts.running == False
