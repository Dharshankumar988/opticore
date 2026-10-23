"""
Configuration and environment variable handling for OptiCore Device Client.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Application configuration loaded from environment variables and .env file."""
    
    def __init__(self, env_file: Optional[str] = None):
        """Load configuration from .env file if it exists."""
        if env_file and Path(env_file).exists():
            load_dotenv(env_file)
        else:
            load_dotenv()
    
    # Server Configuration
    @property
    def OPTICORE_SERVER_URL(self) -> str:
        return os.getenv('OPTICORE_SERVER_URL', 'https://your-ngrok-url.ngrok-free.dev')
    
    @property
    def OPTICORE_CLIENT_ID(self) -> str:
        return os.getenv('OPTICORE_CLIENT_ID', 'opticore-client-1')
    
    # Web Dashboard Configuration
    @property
    def HOST(self) -> str:
        return os.getenv('HOST', '127.0.0.1')
    
    @property
    def PORT(self) -> int:
        return int(os.getenv('PORT', '5050'))
    
    # Camera Configuration
    @property
    def CAMERA_INDEX(self) -> int:
        return int(os.getenv('CAMERA_INDEX', '0'))
    
    @property
    def CAMERA_WIDTH(self) -> int:
        return int(os.getenv('CAMERA_WIDTH', '640'))
    
    @property
    def CAMERA_HEIGHT(self) -> int:
        return int(os.getenv('CAMERA_HEIGHT', '480'))
    
    @property
    def STREAM_FPS(self) -> int:
        return int(os.getenv('STREAM_FPS', '10'))
    
    @property
    def JPEG_QUALITY(self) -> int:
        return int(os.getenv('JPEG_QUALITY', '80'))
    
    @property
    def VIDEO_FILE_PATH(self) -> Optional[str]:
        return os.getenv('VIDEO_FILE_PATH')
    
    # TTS Configuration
    @property
    def TTS_ENABLED(self) -> bool:
        return os.getenv('TTS_ENABLED', 'true').lower() == 'true'
    
    @property
    def TTS_RATE(self) -> int:
        return int(os.getenv('TTS_RATE', '175'))
    
    @property
    def TTS_VOLUME(self) -> float:
        return float(os.getenv('TTS_VOLUME', '0.8'))
    
    @property
    def ALERT_COOLDOWN_SECONDS(self) -> int:
        return int(os.getenv('ALERT_COOLDOWN_SECONDS', '5'))
    
    @property
    def ALERT_VERBOSITY(self) -> str:
        return os.getenv('ALERT_VERBOSITY', 'normal')
    
    # Groq Configuration (Optional)
    @property
    def GROQ_ENABLED(self) -> bool:
        return os.getenv('GROQ_ENABLED', 'false').lower() == 'true'
    
    @property
    def GROQ_API_KEY(self) -> Optional[str]:
        return os.getenv('GROQ_API_KEY')
    
    @property
    def GROQ_MODEL(self) -> str:
        return os.getenv('GROQ_MODEL', 'llama3-8b-8192')
    
    # WebSocket Configuration
    @property
    def WS_MAX_RECONNECT_DELAY(self) -> int:
        return int(os.getenv('WS_MAX_RECONNECT_DELAY', '30'))
    
    @property
    def WS_INITIAL_RECONNECT_DELAY(self) -> int:
        return int(os.getenv('WS_INITIAL_RECONNECT_DELAY', '1'))
    
    @property
    def WS_TIMEOUT(self) -> int:
        return int(os.getenv('WS_TIMEOUT', '10'))
    
    # Frame Buffer Configuration
    @property
    def FRAME_BUFFER_SIZE(self) -> int:
        return int(os.getenv('FRAME_BUFFER_SIZE', '2'))
    
    def validate(self) -> list[str]:
        """Validate required configuration and return list of errors."""
        errors = []
        
        if not self.OPTICORE_SERVER_URL or self.OPTICORE_SERVER_URL == 'https://your-ngrok-url.ngrok-free.dev':
            errors.append("OPTICORE_SERVER_URL must be set to your actual server URL")
        
        if self.GROQ_ENABLED and not self.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is required when GROQ_ENABLED is true")
        
        return errors


# Global configuration instance
config = Config()
