"""
Text-to-Speech (TTS) Engine using Piper TTS (Indic TTS).
Optimized for offline Hindi speech synthesis on ARM devices (Raspberry Pi).
"""
import subprocess
import tempfile
import os
import threading
import wave
import io
from typing import Optional
import config

# Try to import Piper (neural TTS)
try:
    from piper import PiperVoice
    from piper.config import SynthesisConfig
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False
    PiperVoice = None
    SynthesisConfig = None
    print("⚠️  piper-tts not installed. Install with: pip install piper-tts")


class TTSEngine:
    """
    Text-to-speech engine using Piper TTS for high-quality Hindi voice synthesis.
    
    Piper is a fast, local neural TTS system optimized for Raspberry Pi and ARM devices.
    Uses the 'hi_IN-rohan' voice model for Hindi speech.
    """
    
    def __init__(
        self,
        voice: str = "hi_IN-rohan-medium",
        speed: float = 1.0,
    ):
        self.voice = voice
        self.speed = speed
        self._piper_voice = None
        
        # Model directory
        self._model_dir = os.path.join(config.MODEL_DIR, "piper")
        os.makedirs(self._model_dir, exist_ok=True)
        
        # Temp files for audio output
        self._temp_wav = os.path.join(tempfile.gettempdir(), "piper_out.wav")
        
        # Check available tools
        self._use_aplay = self._check_command("aplay")
        self._use_sox = self._check_command("sox")
        
        # Initialize Piper if available
        self._use_piper = False
        if PIPER_AVAILABLE:
            self._init_piper()
        
        if not self._use_piper:
            print("⚠️  Piper TTS not available, using eSpeak-NG fallback")
            self._verify_espeak()
    
    def _init_piper(self) -> None:
        """Initialize Piper TTS with the Hindi model."""
        model_path = os.path.join(self._model_dir, f"{self.voice}.onnx")
        config_path = os.path.join(self._model_dir, f"{self.voice}.onnx.json")
        
        if os.path.exists(model_path):
            try:
                self._piper_voice = PiperVoice.load(model_path, config_path)
                self._use_piper = True
                print(f"✅ Piper TTS loaded: {self.voice}")
            except Exception as e:
                print(f"❌ Failed to load Piper model: {e}")
                self._use_piper = False
        else:
            print(f"⚠️  Piper model not found at: {model_path}")
            print("   Run download_model() to get the Hindi voice model")
    
    def _check_command(self, cmd: str) -> bool:
        """Check if a command is available."""
        try:
            result = subprocess.run(
                ["which", cmd],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except:
            return False
    
    def _verify_espeak(self) -> None:
        """Verify that eSpeak-NG is installed (fallback)."""
        try:
            result = subprocess.run(
                ["espeak-ng", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("eSpeak-NG not working properly")
        except FileNotFoundError:
            raise RuntimeError(
                "Neither Piper TTS nor eSpeak-NG is available. "
                "Please install piper-tts with: pip install piper-tts"
            )
    
    def download_model(self, voice: str = None) -> bool:
        """
        Download the Piper voice model for Hindi.
        
        Args:
            voice: Voice model name (default: hi_IN-rohan-medium)
        
        Returns:
            True if download was successful
        """
        if voice is None:
            voice = self.voice
        
        model_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/rohan/medium/{voice}.onnx"
        config_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/rohan/medium/{voice}.onnx.json"
        
        model_path = os.path.join(self._model_dir, f"{voice}.onnx")
        config_path = os.path.join(self._model_dir, f"{voice}.onnx.json")
        
        print(f"📥 Downloading Piper Hindi voice model: {voice}...")
        
        try:
            # Download model
            subprocess.run([
                "wget", "-q", "--show-progress",
                "-O", model_path,
                model_url
            ], check=True, timeout=300)
            
            # Download config
            subprocess.run([
                "wget", "-q",
                "-O", config_path,
                config_url
            ], check=True, timeout=60)
            
            print(f"✅ Model downloaded to: {model_path}")
            
            # Re-initialize Piper
            self._init_piper()
            return self._use_piper
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to download model: {e}")
            return False
        except subprocess.TimeoutExpired:
            print("❌ Download timed out")
            return False
    
    def speak(self, text: str) -> None:
        """
        Speak the given text using Piper TTS.
        
        Args:
            text: Text to speak (Hindi)
        """
        if not text or not text.strip():
            return
        
        if self._use_piper and self._piper_voice:
            self._speak_piper(text)
        else:
            self._speak_espeak(text)
    
    def _speak_piper(self, text: str) -> None:
        """Speak using Piper TTS (neural voice)."""
        try:
            # Synthesize audio using Piper with speed control
            syn_config = SynthesisConfig(
                length_scale=1.0 / self.speed  # Inverse: lower = faster
            )
            audio_bytes = b""
            for chunk in self._piper_voice.synthesize(text, syn_config):
                audio_bytes += chunk.audio_int16_bytes
            
            # Write to WAV file
            sample_rate = self._piper_voice.config.sample_rate
            with wave.open(self._temp_wav, "wb") as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_bytes)
            
            # Apply audio filtering with sox if available
            if self._use_sox:
                filtered_wav = self._temp_wav.replace(".wav", "_filtered.wav")
                filter_cmd = [
                    "sox", self._temp_wav, filtered_wav,
                    "norm", "-1",           # Normalize audio
                    "highpass", "80",       # Remove low rumble
                ]
                subprocess.run(filter_cmd, capture_output=True, timeout=10)
                play_file = filtered_wav
            else:
                play_file = self._temp_wav
            
            # Play the audio
            if self._use_aplay:
                play_cmd = ["aplay", "-q", play_file]
            else:
                play_cmd = ["paplay", play_file]
            
            subprocess.run(play_cmd, capture_output=True, timeout=60)
            
        except Exception as e:
            print(f"Piper TTS error: {e}")
            self._speak_espeak(text)
    
    def _speak_espeak(self, text: str) -> None:
        """Fallback: Speak using eSpeak-NG."""
        try:
            speed = getattr(config, 'TTS_SPEED', 100)
            pitch = getattr(config, 'TTS_PITCH', 40)
            amplitude = getattr(config, 'TTS_AMPLITUDE', 80)
            gap = getattr(config, 'TTS_GAP', 15)
            
            # Generate WAV file
            raw_wav = os.path.join(tempfile.gettempdir(), "espeak_raw.wav")
            
            synth_cmd = [
                "espeak-ng",
                "-v", "hi",
                "-s", str(speed),
                "-p", str(pitch),
                "-a", str(amplitude),
                "-g", str(gap),
                "-w", raw_wav,
                text
            ]
            subprocess.run(synth_cmd, capture_output=True, timeout=30)
            
            # Apply filtering with sox
            if self._use_sox:
                clean_wav = os.path.join(tempfile.gettempdir(), "espeak_clean.wav")
                filter_cmd = [
                    "sox", raw_wav, clean_wav,
                    "lowpass", "3500",
                    "highpass", "100",
                    "compand", "0.3,1", "6:-70,-60,-20", "-5", "-90", "0.2",
                    "gain", "-n", "-3"
                ]
                subprocess.run(filter_cmd, capture_output=True, timeout=30)
                play_file = clean_wav
            else:
                play_file = raw_wav
            
            # Play audio
            if self._use_aplay:
                play_cmd = ["aplay", "-q", "--buffer-size=65536", play_file]
            else:
                play_cmd = ["paplay", play_file]
            
            subprocess.run(play_cmd, capture_output=True, timeout=60)
            
        except subprocess.TimeoutExpired:
            print("TTS timeout")
        except Exception as e:
            print(f"eSpeak TTS error: {e}")
    
    def speak_async(self, text: str) -> threading.Thread:
        """Speak text asynchronously."""
        thread = threading.Thread(target=self.speak, args=(text,), daemon=True)
        thread.start()
        return thread
    
    def speak_to_file(self, text: str, filepath: Optional[str] = None) -> str:
        """Generate speech and save to a WAV file."""
        if filepath is None:
            filepath = self._temp_wav
        
        if self._use_piper and self._piper_voice:
            audio_bytes = b""
            for chunk in self._piper_voice.synthesize(text):
                audio_bytes += chunk.audio_int16_bytes
            
            with wave.open(filepath, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self._piper_voice.config.sample_rate)
                wav_file.writeframes(audio_bytes)
        else:
            cmd = [
                "espeak-ng",
                "-v", "hi",
                "-w", filepath,
                text
            ]
            subprocess.run(cmd, capture_output=True, timeout=30)
        
        return filepath
    
    def set_speed(self, speed: float) -> None:
        """Set speech speed (0.5 = slow, 1.0 = normal, 2.0 = fast)."""
        self.speed = max(0.5, min(2.0, speed))
    
    def set_voice(self, voice: str) -> None:
        """Set the voice model name and reload."""
        self.voice = voice
        if PIPER_AVAILABLE:
            self._init_piper()
    
    def is_piper_available(self) -> bool:
        """Check if Piper TTS is available and ready."""
        return self._use_piper and self._piper_voice is not None
    
    def get_status(self) -> dict:
        """Get TTS engine status."""
        return {
            "engine": "piper" if self._use_piper else "espeak-ng",
            "voice": self.voice,
            "speed": self.speed,
            "sox_filtering": self._use_sox,
            "piper_loaded": self._piper_voice is not None,
        }


if __name__ == "__main__":
    print("🎤 Testing Indic TTS Engine (Piper)...\n")
    
    tts = TTSEngine()
    status = tts.get_status()
    
    print(f"Engine: {status['engine']}")
    print(f"Voice: {status['voice']}")
    print(f"Piper loaded: {status['piper_loaded']}")
    print(f"Sox filtering: {status['sox_filtering']}")
    
    if not tts.is_piper_available():
        print("\n⚠️  Piper model not found. Downloading...")
        if tts.download_model():
            print("✅ Model ready!")
        else:
            print("❌ Using eSpeak-NG fallback")
    
    print("\n🔊 Speaking test phrase...")
    tts.speak("नमस्ते। मैं पाइपर टी टी एस का उपयोग कर रहा हूं। यह एक उच्च गुणवत्ता वाली आवाज़ है।")
    print("✅ Done!")
