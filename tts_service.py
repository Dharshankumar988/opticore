"""
Text-to-speech service for OptiCore Device Client.
"""
import threading
import queue
import logging
import time
from typing import Optional
import pyttsx3

logger = logging.getLogger(__name__)


class TTSService:
    """Manages text-to-speech generation and playback."""
    
    def __init__(self, enabled: bool = True, rate: int = 175, volume: float = 0.8):
        self.enabled = enabled
        self.rate = rate
        self.volume = volume
        
        self.engine: Optional[pyttsx3.Engine] = None
        self.speech_queue: queue.Queue = queue.Queue()
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.currently_speaking = False
        self.stop_requested = False
        
        self.lock = threading.Lock()
    
    def initialize(self) -> bool:
        """Initialize TTS engine."""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            return False
    
    def start(self):
        """Start TTS worker thread."""
        if self.running:
            return
        
        if not self.enabled:
            logger.info("TTS is disabled")
            return
        
        if not self.engine and not self.initialize():
            logger.warning("TTS engine not available, speech will be silent")
            return
        
        self.running = True
        self.stop_requested = False
        self.worker_thread = threading.Thread(target=self._speech_loop, daemon=True)
        self.worker_thread.start()
    
    def stop(self):
        """Stop TTS worker thread."""
        self.running = False
        self.stop_requested = True
        
        if self.worker_thread:
            self.worker_thread.join(timeout=2.0)
        
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
    
    def speak(self, text: str, priority: bool = False):
        """Queue text for speech. Priority messages skip the queue."""
        if not self.enabled:
            return
        
        if priority:
            # Insert at front of queue
            temp_queue = queue.Queue()
            temp_queue.put(text)
            while not self.speech_queue.empty():
                temp_queue.put(self.speech_queue.get())
            self.speech_queue = temp_queue
        else:
            self.speech_queue.put(text)
    
    def stop_speech(self):
        """Stop current speech and clear queue."""
        with self.lock:
            self.stop_requested = True
            if self.engine:
                try:
                    self.engine.stop()
                except:
                    pass
            # Clear queue
            while not self.speech_queue.empty():
                try:
                    self.speech_queue.get_nowait()
                except queue.Empty:
                    pass
            self.stop_requested = False
            self.currently_speaking = False
    
    def _speech_loop(self):
        """Worker thread for speech playback."""
        while self.running:
            try:
                # Get next message with timeout
                text = self.speech_queue.get(timeout=0.5)
                
                if self.stop_requested:
                    continue
                
                with self.lock:
                    self.currently_speaking = True
                
                # Speak the text
                if self.engine:
                    try:
                        self.engine.say(text)
                        self.engine.runAndWait()
                    except Exception as e:
                        logger.error(f"Speech error: {e}")
                
                with self.lock:
                    self.currently_speaking = False
                    self.stop_requested = False
            
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Speech loop error: {e}")
                with self.lock:
                    self.currently_speaking = False
    
    def set_rate(self, rate: int):
        """Set speech rate."""
        self.rate = rate
        if self.engine:
            try:
                self.engine.setProperty('rate', rate)
            except:
                pass
    
    def set_volume(self, volume: float):
        """Set speech volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        if self.engine:
            try:
                self.engine.setProperty('volume', self.volume)
            except:
                pass
    
    def get_available_voices(self) -> list:
        """Get list of available voices."""
        if self.engine:
            try:
                voices = self.engine.getProperty('voices')
                return [(voice.id, voice.name) for voice in voices] if voices else []
            except:
                pass
        return []
    
    def set_voice(self, voice_id: str):
        """Set voice by ID."""
        if self.engine:
            try:
                voices = self.engine.getProperty('voices')
                for voice in voices:
                    if voice.id == voice_id:
                        self.engine.setProperty('voice', voice.id)
                        return True
            except:
                pass
        return False
    
    def test_speech(self):
        """Test speech with a sample message."""
        self.speak("OptiCore text-to-speech test.", priority=True)
    
    def get_stats(self) -> dict:
        """Get TTS statistics."""
        return {
            'enabled': self.enabled,
            'running': self.running,
            'currently_speaking': self.currently_speaking,
            'queue_size': self.speech_queue.qsize(),
            'rate': self.rate,
            'volume': self.volume
        }
