"""
Tests for configuration handling.
"""
import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config


def test_config_defaults():
    """Test that configuration has sensible defaults."""
    config = Config()
    
    assert config.HOST == '127.0.0.1'
    assert config.PORT == 5050
    assert config.CAMERA_INDEX == 0
    assert config.CAMERA_WIDTH == 640
    assert config.CAMERA_HEIGHT == 480
    assert config.STREAM_FPS == 10
    assert config.JPEG_QUALITY == 80
    assert config.TTS_ENABLED == True
    assert config.TTS_RATE == 175
    assert config.TTS_VOLUME == 0.8
    assert config.GROQ_ENABLED == False


def test_config_from_env():
    """Test that configuration loads from environment variables."""
    os.environ['OPTICORE_SERVER_URL'] = 'https://test.example.com'
    os.environ['CAMERA_INDEX'] = '1'
    os.environ['TTS_ENABLED'] = 'false'
    
    config = Config()
    
    assert config.OPTICORE_SERVER_URL == 'https://test.example.com'
    assert config.CAMERA_INDEX == 1
    assert config.TTS_ENABLED == False
    
    # Cleanup
    del os.environ['OPTICORE_SERVER_URL']
    del os.environ['CAMERA_INDEX']
    del os.environ['TTS_ENABLED']


def test_config_validation():
    """Test configuration validation."""
    # Missing server URL should produce error
    os.environ['OPTICORE_SERVER_URL'] = 'https://your-ngrok-url.ngrok-free.dev'
    config = Config()
    errors = config.validate()
    assert len(errors) > 0
    assert 'OPTICORE_SERVER_URL' in errors[0]
    
    # Valid server URL should not produce error
    os.environ['OPTICORE_SERVER_URL'] = 'https://real-server.example.com'
    config = Config()
    errors = config.validate()
    assert not any('OPTICORE_SERVER_URL' in e for e in errors)
    
    # Cleanup
    del os.environ['OPTICORE_SERVER_URL']


def test_groq_validation():
    """Test Groq configuration validation."""
    # Groq validation is non-fatal - should not block startup
    # Groq enabled without API key should NOT produce error (it's optional)
    os.environ['GROQ_ENABLED'] = 'true'
    os.environ['GROQ_API_KEY'] = ''
    config = Config()
    errors = config.validate()
    assert not any('GROQ_API_KEY' in e for e in errors)
    
    # Groq enabled with API key should also not produce error
    os.environ['GROQ_API_KEY'] = 'test-key'
    config = Config()
    errors = config.validate()
    assert not any('GROQ_API_KEY' in e for e in errors)
    
    # Cleanup
    del os.environ['GROQ_ENABLED']
    del os.environ['GROQ_API_KEY']
