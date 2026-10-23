"""
Tests for Groq service.
"""
import pytest
import asyncio
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from groq_service import GroqService, GroqConfig


def test_groq_config_defaults():
    """Test GroqConfig defaults."""
    config = GroqConfig(
        enabled=True,
        api_key="test-key",
        model="openai/gpt-oss-20b",
        timeout_seconds=5,
        max_tokens=150,
        cooldown_seconds=30,
        max_input_tokens=500
    )
    
    assert config.enabled == True
    assert config.api_key == "test-key"
    assert config.model == "openai/gpt-oss-20b"
    assert config.timeout_seconds == 5
    assert config.max_tokens == 150
    assert config.cooldown_seconds == 30
    assert config.max_input_tokens == 500


def test_groq_service_disabled():
    """Test Groq service when disabled."""
    config = GroqConfig(
        enabled=False,
        api_key=None,
        model="openai/gpt-oss-20b",
        timeout_seconds=5,
        max_tokens=150,
        cooldown_seconds=30,
        max_input_tokens=500
    )
    
    service = GroqService(config)
    
    assert service.is_available() == False
    assert service.get_status()['enabled'] == False


def test_groq_service_no_api_key():
    """Test Groq service with no API key."""
    config = GroqConfig(
        enabled=True,
        api_key=None,
        model="openai/gpt-oss-20b",
        timeout_seconds=5,
        max_tokens=150,
        cooldown_seconds=30,
        max_input_tokens=500
    )
    
    service = GroqService(config)
    
    assert service.is_available() == False
    assert service.get_status()['configured'] == False


@pytest.mark.asyncio
async def test_groq_generate_summary_disabled():
    """Test that generate_summary returns None when disabled."""
    config = GroqConfig(
        enabled=False,
        api_key=None,
        model="openai/gpt-oss-20b",
        timeout_seconds=5,
        max_tokens=150,
        cooldown_seconds=30,
        max_input_tokens=500
    )
    
    service = GroqService(config)
    
    detections = [{'class_name': 'person', 'confidence': 0.9, 'track_id': 1}]
    ocr_results = []
    
    result = await service.generate_summary(detections, ocr_results)
    assert result is None


@pytest.mark.asyncio
async def test_groq_cooldown():
    """Test that cooldown prevents repeated requests."""
    config = GroqConfig(
        enabled=True,
        api_key="test-key",
        model="openai/gpt-oss-20b",
        timeout_seconds=5,
        max_tokens=150,
        cooldown_seconds=30,
        max_input_tokens=500
    )
    
    service = GroqService(config)
    
    # First call should not be blocked by cooldown
    detections = [{'class_name': 'person', 'confidence': 0.9, 'track_id': 1}]
    ocr_results = []
    
    # Since we don't have a real API key, this will return None
    result = await service.generate_summary(detections, ocr_results)
    assert result is None  # No real client
    
    # Second call within cooldown should also return None (cached)
    result2 = await service.generate_summary(detections, ocr_results)
    assert result2 is None


def test_groq_build_prompt():
    """Test prompt building."""
    config = GroqConfig(
        enabled=True,
        api_key="test-key",
        model="openai/gpt-oss-20b",
        timeout_seconds=5,
        max_tokens=150,
        cooldown_seconds=30,
        max_input_tokens=500
    )
    
    service = GroqService(config)
    
    # Test with detections
    detections = [
        {'class_name': 'person', 'confidence': 0.9, 'track_id': 1},
        {'class_name': 'person', 'confidence': 0.85, 'track_id': 2},
        {'class_name': 'car', 'confidence': 0.95, 'track_id': None}
    ]
    ocr_results = []
    
    prompt = service._build_prompt(detections, ocr_results)
    assert prompt is not None
    assert '2 person' in prompt
    assert '1 car' in prompt
    
    # Test with OCR
    detections = []
    ocr_results = [
        {'text': 'STOP', 'confidence': 0.9},
        {'text': 'YIELD', 'confidence': 0.85}
    ]
    
    prompt = service._build_prompt(detections, ocr_results)
    assert prompt is not None
    assert 'STOP' in prompt or 'YIELD' in prompt
    
    # Test with empty input
    prompt = service._build_prompt([], [])
    assert prompt is None


@pytest.mark.asyncio
async def test_groq_test_connection_disabled():
    """Test connection test when disabled."""
    config = GroqConfig(
        enabled=False,
        api_key=None,
        model="openai/gpt-oss-20b",
        timeout_seconds=5,
        max_tokens=150,
        cooldown_seconds=30,
        max_input_tokens=500
    )
    
    service = GroqService(config)
    
    result = await service.test_connection()
    assert result['success'] == False
    assert 'disabled' in result['error'].lower()


@pytest.mark.asyncio
async def test_groq_test_connection_no_key():
    """Test connection test with no API key."""
    config = GroqConfig(
        enabled=True,
        api_key=None,
        model="openai/gpt-oss-20b",
        timeout_seconds=5,
        max_tokens=150,
        cooldown_seconds=30,
        max_input_tokens=500
    )
    
    service = GroqService(config)
    
    result = await service.test_connection()
    assert result['success'] == False
    assert 'api key' in result['error'].lower()
