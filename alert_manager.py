"""
Alert prioritization, deduplication and speech throttling for OptiCore Device Client.
"""
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """Represents an alert with deduplication tracking."""
    message: str
    priority: int  # 1-10, higher is more urgent
    alert_type: str  # 'obstacle', 'person', 'vehicle', 'text', 'info'
    timestamp: float = field(default_factory=time.time)
    track_id: Optional[int] = None
    spoken: bool = False


class AlertManager:
    """Manages alert prioritization, deduplication and throttling."""
    
    def __init__(self, cooldown_seconds: int = 5, verbosity: str = 'normal'):
        self.cooldown_seconds = cooldown_seconds
        self.verbosity = verbosity
        
        self.alert_history: Dict[str, float] = {}  # alert_key -> last_spoken_time
        self.track_history: Dict[int, float] = {}  # track_id -> last_spoken_time
        self.pending_alerts: List[Alert] = []
        self.lock = False
        
        # Alert type priorities (higher = more urgent)
        self.priority_map = {
            'obstacle': 9,
            'person': 7,
            'vehicle': 6,
            'text': 5,
            'info': 3
        }
    
    def add_detection_alert(self, class_name: str, confidence: float, 
                          track_id: Optional[int] = None, bbox: Optional[list] = None) -> Optional[str]:
        """Add a detection alert and return message if should speak."""
        # Determine alert type and priority
        alert_type = self._classify_detection(class_name)
        priority = self.priority_map.get(alert_type, 3)
        
        # Check if this is a high-priority obstacle
        if alert_type == 'obstacle' and confidence > 0.7:
            # Check if obstacle is close (simple heuristic based on bbox size)
            if bbox and len(bbox) == 4:
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                area = width * height
                # Large bbox = close obstacle
                if area > 100000:  # Adjust based on your resolution
                    message = f"Warning: {class_name} nearby"
                    if self._should_speak(message, track_id, priority):
                        return message
        
        # Normal detection alert
        if self.verbosity == 'minimal':
            return None
        
        # Deduplicate by track ID if available
        if track_id is not None:
            if self._is_on_cooldown_track(track_id):
                return None
        
        # Deduplicate by class name
        alert_key = f"detection:{class_name}"
        if self._is_on_cooldown(alert_key):
            return None
        
        message = self._format_detection_message(class_name, confidence)
        if self._should_speak(message, track_id, priority):
            self._record_spoken(alert_key, track_id)
            return message
        
        return None
    
    def add_ocr_alert(self, text: str, confidence: float) -> Optional[str]:
        """Add an OCR alert and return message if should speak."""
        if not text or len(text.strip()) < 2:
            return None
        
        if self.verbosity == 'minimal':
            return None
        
        # Sanitize text
        sanitized = self._sanitize_text(text)
        if not sanitized:
            return None
        
        alert_key = f"ocr:{sanitized[:20]}"
        if self._is_on_cooldown(alert_key):
            return None
        
        message = f"It says, \"{sanitized}\""
        if self._should_speak(message, None, self.priority_map['text']):
            self._record_spoken(alert_key, None)
            return message
        
        return None
    
    def add_proximity_alert(self, message: str) -> Optional[str]:
        """Add a high-priority proximity alert."""
        alert_key = f"proximity:{message}"
        if self._is_on_cooldown(alert_key):
            return None
        
        if self._should_speak(message, None, self.priority_map['obstacle']):
            self._record_spoken(alert_key, None)
            return message
        
        return None
    
    def _classify_detection(self, class_name: str) -> str:
        """Classify detection into alert type."""
        class_lower = class_name.lower()
        
        obstacles = ['obstacle', 'barrier', 'wall', 'stair', 'step', 'hole', 'pit']
        if any(obs in class_lower for obs in obstacles):
            return 'obstacle'
        
        people = ['person', 'human', 'man', 'woman', 'child']
        if any(p in class_lower for p in people):
            return 'person'
        
        vehicles = ['car', 'truck', 'bus', 'motorcycle', 'bicycle', 'bike']
        if any(v in class_lower for v in vehicles):
            return 'vehicle'
        
        return 'info'
    
    def _format_detection_message(self, class_name: str, confidence: float) -> str:
        """Format detection into speech message."""
        if confidence > 0.8:
            return f"{class_name}"
        elif confidence > 0.5:
            return f"Possible {class_name}"
        else:
            return f"Uncertain {class_name}"
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize OCR text for safe speech."""
        # Remove potentially dangerous characters
        text = text.strip()
        # Limit length
        if len(text) > 100:
            text = text[:100] + "..."
        # Remove control characters
        text = ''.join(char for char in text if char.isprint() or char.isspace())
        return text
    
    def _is_on_cooldown(self, alert_key: str) -> bool:
        """Check if alert is on cooldown."""
        last_spoken = self.alert_history.get(alert_key, 0)
        return (time.time() - last_spoken) < self.cooldown_seconds
    
    def _is_on_cooldown_track(self, track_id: int) -> bool:
        """Check if track ID is on cooldown."""
        last_spoken = self.track_history.get(track_id, 0)
        return (time.time() - last_spoken) < self.cooldown_seconds
    
    def _should_speak(self, message: str, track_id: Optional[int], priority: int) -> bool:
        """Determine if alert should be spoken based on priority and cooldown."""
        # High priority alerts can bypass cooldown
        if priority >= 8:
            return True
        
        # Check cooldown
        if track_id is not None and self._is_on_cooldown_track(track_id):
            return False
        
        return True
    
    def _record_spoken(self, alert_key: str, track_id: Optional[int]):
        """Record that an alert was spoken."""
        self.alert_history[alert_key] = time.time()
        if track_id is not None:
            self.track_history[track_id] = time.time()
    
    def clear_history(self):
        """Clear alert history (useful for testing or reset)."""
        self.alert_history.clear()
        self.track_history.clear()
    
    def get_stats(self) -> dict:
        """Get alert manager statistics."""
        return {
            'cooldown_seconds': self.cooldown_seconds,
            'verbosity': self.verbosity,
            'alerts_tracked': len(self.alert_history),
            'tracks_tracked': len(self.track_history)
        }
