"""
Automatic Speech Recognition (ASR) Engine using Vosk.
Optimized for low-latency offline Hindi speech-to-text.
"""
import os
import json
import wave
from typing import Optional, Generator, List
from vosk import Model, KaldiRecognizer, SetLogLevel
import config

# Suppress Vosk debug logs
SetLogLevel(-1)


class ASREngine:
    """
    Optimized speech recognition engine using Vosk with Hindi model.
    
    Key optimizations:
    - Reuses recognizer instance when possible
    - Processes audio in optimized chunk sizes
    - Provides streaming recognition for real-time feedback
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the ASR engine with a Vosk model.
        
        Args:
            model_path: Path to the Vosk model directory.
                       Defaults to config.VOSK_MODEL_PATH
        """
        self.model_path = model_path or config.VOSK_MODEL_PATH
        self.sample_rate = config.AUDIO_SAMPLE_RATE
        self.model: Optional[Model] = None
        self.recognizer: Optional[KaldiRecognizer] = None
        
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the Vosk model from disk."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Vosk model not found at: {self.model_path}\n"
                f"Please run setup.sh to download the Hindi model."
            )
        
        print(f"Loading Vosk model from: {self.model_path}")
        self.model = Model(self.model_path)
        self._create_recognizer()
        print("Model loaded successfully!")
    
    def _create_recognizer(self) -> None:
        """Create a new recognizer instance."""
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
        # Disable word-level results for faster processing
        self.recognizer.SetWords(False)
        # Enable partial results for real-time feedback
        self.recognizer.SetPartialWords(False)
    
    def reset_recognizer(self) -> None:
        """Reset the recognizer for a new utterance."""
        if self.model is not None:
            self._create_recognizer()
    
    def process_audio_chunk(self, audio_chunk: bytes) -> Optional[str]:
        """
        Process a chunk of audio and return partial result if available.
        
        Args:
            audio_chunk: Raw audio bytes (16-bit PCM)
            
        Returns:
            Partial transcription or None if no result yet
        """
        if self.recognizer.AcceptWaveform(audio_chunk):
            result = json.loads(self.recognizer.Result())
            return result.get("text", "")
        else:
            partial = json.loads(self.recognizer.PartialResult())
            return partial.get("partial", "")
    
    def get_final_result(self) -> str:
        """Get the final recognition result."""
        result = json.loads(self.recognizer.FinalResult())
        return result.get("text", "")
    
    def transcribe_stream(
        self, 
        audio_stream: Generator[bytes, None, None]
    ) -> Generator[str, None, None]:
        """
        Transcribe a stream of audio chunks in real-time.
        
        Args:
            audio_stream: Generator yielding audio chunks
            
        Yields:
            Transcription results (partial and final)
        """
        self.reset_recognizer()
        
        for chunk in audio_stream:
            if self.recognizer.AcceptWaveform(chunk):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "")
                if text:
                    yield text
        
        # Get final result
        final = self.get_final_result()
        if final:
            yield final
    
    def transcribe_file(self, filepath: str) -> str:
        """
        Transcribe audio from a WAV file.
        
        Args:
            filepath: Path to the WAV file
            
        Returns:
            Transcribed text
        """
        self.reset_recognizer()
        
        with wave.open(filepath, 'rb') as wf:
            if wf.getnchannels() != 1:
                raise ValueError("Audio must be mono")
            if wf.getsampwidth() != 2:
                raise ValueError("Audio must be 16-bit")
            if wf.getframerate() != self.sample_rate:
                raise ValueError(f"Sample rate must be {self.sample_rate}")
            
            # Use larger chunks for file processing (more efficient)
            chunk_size = 4000
            while True:
                data = wf.readframes(chunk_size)
                if len(data) == 0:
                    break
                self.recognizer.AcceptWaveform(data)
        
        return self.get_final_result()
    
    def transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribe raw audio data with optimized processing.
        
        Args:
            audio_data: Raw audio bytes (16-bit PCM, mono)
            
        Returns:
            Transcribed text
        """
        self.reset_recognizer()
        
        # Use larger chunks for batch processing (faster than small chunks)
        # 4000 samples = 250ms at 16kHz, good balance of speed/accuracy
        chunk_samples = 4000
        chunk_size = chunk_samples * 2  # 2 bytes per 16-bit sample
        offset = 0
        
        while offset < len(audio_data):
            chunk = audio_data[offset:offset + chunk_size]
            self.recognizer.AcceptWaveform(chunk)
            offset += chunk_size
        
        return self.get_final_result()
    
    def transcribe_audio_streaming(
        self, 
        audio_data: bytes
    ) -> Generator[str, None, None]:
        """
        Transcribe audio with streaming results for real-time feedback.
        
        Args:
            audio_data: Raw audio bytes
            
        Yields:
            Partial and final transcription results
        """
        self.reset_recognizer()
        
        chunk_size = config.AUDIO_CHUNK_SIZE * 2
        offset = 0
        
        while offset < len(audio_data):
            chunk = audio_data[offset:offset + chunk_size]
            if self.recognizer.AcceptWaveform(chunk):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "")
                if text:
                    yield text
            offset += chunk_size
        
        final = self.get_final_result()
        if final:
            yield final


if __name__ == "__main__":
    # Test ASR engine
    engine = ASREngine()
    print("ASR Engine initialized successfully!")
    print(f"Model path: {engine.model_path}")
