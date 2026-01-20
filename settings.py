"""
Configuration configuration management.
"""
import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Any
from logger import get_logger

logger = get_logger("settings")

@dataclass
class AudioSettings:
    sample_rate: int = 16000
    channels: int = 1
    width: int = 2
    chunk_size: int = 1600  # 100ms
    buffer_size: int = 4096

@dataclass
class TTSSettings:
    voice: str = "hi"
    speed: int = 100
    pitch: int = 40
    amplitude: int = 80
    gap: int = 15

@dataclass
class AppSettings:
    base_dir: str
    model_path: str
    wake_words: List[str]
    silence_timeout: float = 1.2
    listen_timeout: float = 10.0
    audio: AudioSettings = field(default_factory=AudioSettings)
    tts: TTSSettings = field(default_factory=TTSSettings)
    commands: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls) -> 'AppSettings':
        """Load configuration from files and environment."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, "data")
        model_dir = os.path.join(base_dir, "models")
        
        # Load Intents
        intents_path = os.path.join(data_dir, "intents.json")
        commands = {}
        try:
            with open(intents_path, 'r', encoding='utf-8') as f:
                commands = json.load(f)
            logger.info(f"Loaded {len(commands)} commands from {intents_path}")
        except FileNotFoundError:
            logger.error(f"Intents file not found at {intents_path}")
            # Fallback or empty? Better to fail fast or provide defaults?
            # For now, empty dict, but app is useless without commands.

        return cls(
            base_dir=base_dir,
            model_path=os.path.join(model_dir, "vosk-model-small-hi-0.22"),
            wake_words=["सुनो", "हेलो", "ओके"],
            commands=commands
        )

# Global singleton instance
settings = AppSettings.load()
