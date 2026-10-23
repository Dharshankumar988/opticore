"""
Groq LLM service for optional natural-language scene summaries.
Designed to be completely optional and non-blocking.
"""
import asyncio
import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class GroqConfig:
    """Groq service configuration."""
    enabled: bool
    api_key: Optional[str]
    model: str
    timeout_seconds: int
    max_tokens: int
    cooldown_seconds: int
    max_input_tokens: int


class GroqService:
    """Groq LLM service with async, timeout, and deduplication."""
    
    def __init__(self, config: GroqConfig):
        self.config = config
        self._client = None
        self._last_request_time = 0.0
        self._last_summary = ""
        self._available = False
        self._init_attempted = False
        
        if self.config.enabled and self.config.api_key:
            self._initialize()
    
    def _initialize(self):
        """Initialize Groq client (lazy, non-blocking)."""
        if self._init_attempted:
            return

        self._init_attempted = True

        try:
            from groq import Groq as GroqClient
            self._client = GroqClient(api_key=self.config.api_key)
            logger.info("Groq client initialized")
        except ImportError:
            logger.warning("Groq library not installed. Install with: pip install groq")
            return
        except Exception as e:
            logger.warning(f"Failed to initialize Groq client: {e}")
            self._client = None  # Ensure client is None on failure
            return
    
    def is_available(self) -> bool:
        """Check if Groq service is available and ready."""
        if not self.config.enabled:
            return False
        if not self.config.api_key:
            return False
        if not self._client:
            return False
        return self._available
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            'enabled': self.config.enabled,
            'configured': bool(self.config.api_key),
            'available': self.is_available(),
            'model': self.config.model if self.config.enabled else None,
            'last_request_time': self._last_request_time
        }
    
    async def generate_summary(
        self,
        detections: list[Dict[str, Any]],
        ocr_results: list[Dict[str, Any]],
        force: bool = False
    ) -> Optional[str]:
        """
        Generate a natural-language summary of the current scene.
        
        Args:
            detections: List of detection objects with class_name, confidence, track_id
            ocr_results: List of OCR results with text, confidence
            force: Force generation even if cooldown hasn't elapsed
        
        Returns:
            Summary string or None if disabled/unavailable
        """
        # Fast path: disabled
        if not self.config.enabled:
            return None
        
        # Fast path: not configured
        if not self.config.api_key or not self._client:
            if not self._init_attempted:
                self._initialize()
            if not self._client:
                return None
        
        # Check cooldown
        now = time.time()
        if not force and (now - self._last_request_time) < self.config.cooldown_seconds:
            logger.debug("Groq cooldown active, returning cached summary")
            return self._last_summary if self._last_summary else None
        
        # Build compact input
        prompt = self._build_prompt(detections, ocr_results)
        if not prompt:
            return None
        
        # Async API call with timeout
        try:
            summary = await asyncio.wait_for(
                self._call_groq_async(prompt),
                timeout=self.config.timeout_seconds
            )
            
            if summary:
                self._last_request_time = now
                self._last_summary = summary
                self._available = True
                logger.info(f"Groq summary generated: {summary[:50]}...")
                return summary
            else:
                return None
                
        except asyncio.TimeoutError:
            logger.warning("Groq request timed out")
            self._available = False
            return None
        except Exception as e:
            logger.warning(f"Groq request failed: {e}")
            self._available = False
            return None
    
    def _build_prompt(
        self,
        detections: list[Dict[str, Any]],
        ocr_results: list[Dict[str, Any]]
    ) -> Optional[str]:
        """Build a compact prompt from detections and OCR."""
        parts = []
        
        if detections:
            # Summarize detections by class
            class_counts: Dict[str, int] = {}
            for det in detections:
                class_name = det.get('class_name', 'unknown')
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
            
            det_summary = ", ".join(f"{count} {cls}" for cls, count in class_counts.items())
            parts.append(f"Detected: {det_summary}")
        
        if ocr_results:
            # Take only first few OCR results to stay within token limits
            ocr_texts = [ocr.get('text', '') for ocr in ocr_results[:3] if ocr.get('text')]
            if ocr_texts:
                parts.append(f"Text: {', '.join(ocr_texts[:2])}")
        
        if not parts:
            return None
        
        scene_description = " | ".join(parts)
        
        # Keep prompt compact
        prompt = f"Scene: {scene_description}. Provide a brief 1-sentence natural language summary."
        
        # Truncate if too long (rough estimate: 4 chars per token)
        max_chars = self.config.max_input_tokens * 4
        if len(prompt) > max_chars:
            prompt = prompt[:max_chars] + "..."
        
        return prompt
    
    async def _call_groq_async(self, prompt: str) -> Optional[str]:
        """Async wrapper for Groq API call."""
        # Run in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._call_groq_sync, prompt)
    
    def _call_groq_sync(self, prompt: str) -> Optional[str]:
        """Synchronous Groq API call."""
        try:
            response = self._client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides brief, factual summaries of visual scenes."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=0.3
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            return None
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test Groq connection and model availability.
        Makes a minimal API request to verify everything works.
        """
        result = {
            'success': False,
            'error': None,
            'model': self.config.model,
            'latency_ms': None
        }
        
        if not self.config.enabled:
            result['error'] = 'Groq is disabled'
            return result
        
        if not self.config.api_key:
            result['error'] = 'No API key configured'
            return result
        
        if not self._client:
            self._initialize()
            if not self._client:
                result['error'] = 'Failed to initialize Groq client'
                return result
        
        try:
            start_time = time.time()
            response = await asyncio.wait_for(
                self._call_groq_async("Test"),
                timeout=self.config.timeout_seconds
            )
            latency_ms = (time.time() - start_time) * 1000
            
            result['success'] = True
            result['latency_ms'] = round(latency_ms, 2)
            self._available = True
            logger.info(f"Groq connection test successful: {latency_ms:.2f}ms")
            
        except asyncio.TimeoutError:
            result['error'] = 'Request timed out'
            self._available = False
        except Exception as e:
            result['error'] = str(e)
            self._available = False
        
        return result
