"""
Audio Input/Output module for the Hindi Voice Assistant.
Optimized for low-latency recording and smooth playback.
"""
import pyaudio
import wave
import numpy as np
import os
import tempfile
from typing import Optional, Generator, Tuple
import config


class AudioRecorder:
    """
    Optimized microphone input handler.
    
    Key optimizations:
    - Smaller chunk sizes for faster VAD response
    - Pre-allocated NumPy buffer for efficient processing
    - Adaptive threshold for better speech detection
    """
    
    def __init__(
        self,
        sample_rate: int = config.AUDIO_SAMPLE_RATE,
        channels: int = config.AUDIO_CHANNELS,
        chunk_size: int = config.AUDIO_CHUNK_SIZE
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format = pyaudio.paInt16
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        
        # Pre-allocate buffer for efficiency
        self._buffer = np.zeros(chunk_size, dtype=np.int16)
        
        # Adaptive threshold tracking
        self._noise_floor = 200
        self._noise_samples = []
        
    def start_stream(self) -> None:
        """Start the audio input stream with optimized settings."""
        if self.stream is None or not self.stream.is_active():
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=None  # Blocking mode for predictable latency
            )
    
    def stop_stream(self) -> None:
        """Stop the audio input stream."""
        if self.stream is not None:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
            self.stream = None
    
    def read_chunk(self) -> bytes:
        """Read a single chunk of audio data."""
        if self.stream is None:
            self.start_stream()
        return self.stream.read(self.chunk_size, exception_on_overflow=False)
    
    def stream_audio(self) -> Generator[bytes, None, None]:
        """Generator that yields audio chunks continuously."""
        self.start_stream()
        try:
            while True:
                yield self.read_chunk()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_stream()
    
    def record_audio(self, duration: float) -> bytes:
        """Record audio for a specified duration in seconds."""
        self.start_stream()
        frames = []
        num_chunks = int(self.sample_rate / self.chunk_size * duration)
        
        for _ in range(num_chunks):
            data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            frames.append(data)
        
        return b''.join(frames)
    
    def save_to_wav(self, audio_data: bytes, filepath: str) -> None:
        """Save audio data to a WAV file."""
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data)
    
    def is_speech(self, audio_chunk: bytes, threshold: Optional[int] = None) -> bool:
        """
        Check if audio chunk contains speech with adaptive threshold.
        
        Args:
            audio_chunk: Raw audio bytes
            threshold: Optional fixed threshold (uses adaptive if None)
            
        Returns:
            True if speech detected
        """
        audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
        amplitude = np.abs(audio_array).mean()
        
        # Use adaptive threshold if not specified
        if threshold is None:
            # Update noise floor during silence
            if amplitude < self._noise_floor * 1.5:
                self._noise_samples.append(amplitude)
                if len(self._noise_samples) > 50:
                    self._noise_samples.pop(0)
                if self._noise_samples:
                    self._noise_floor = np.mean(self._noise_samples) * 1.2
            
            # Speech is significantly above noise floor
            threshold = max(300, self._noise_floor * 2.5)
        
        return amplitude > threshold
    
    def get_audio_level(self, audio_chunk: bytes) -> Tuple[float, float]:
        """
        Get audio amplitude and RMS level.
        
        Returns:
            Tuple of (amplitude, rms)
        """
        audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
        amplitude = np.abs(audio_array).mean()
        rms = np.sqrt(np.mean(audio_array.astype(float) ** 2))
        return amplitude, rms
    
    def test_recording(self, duration: int = 3) -> str:
        """Test recording functionality and save to temp file."""
        print(f"Recording for {duration} seconds...")
        audio_data = self.record_audio(duration)
        
        temp_file = os.path.join(tempfile.gettempdir(), "test_recording.wav")
        self.save_to_wav(audio_data, temp_file)
        print(f"Recording saved to: {temp_file}")
        
        return temp_file
    
    def cleanup(self) -> None:
        """Clean up audio resources."""
        self.stop_stream()
        try:
            self.audio.terminate()
        except:
            pass
    
    def __del__(self):
        self.cleanup()


class AudioPlayer:
    """
    Optimized audio playback handler.
    
    Key optimizations:
    - Larger buffer size for smoother playback
    - Pre-opened audio stream for reduced latency
    """
    
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.buffer_size = getattr(config, 'AUDIO_BUFFER_SIZE', 4096)
    
    def play_wav(self, filepath: str) -> None:
        """Play a WAV file with optimized buffering."""
        with wave.open(filepath, 'rb') as wf:
            stream = self.audio.open(
                format=self.audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
                frames_per_buffer=self.buffer_size
            )
            
            data = wf.readframes(self.buffer_size)
            
            while data:
                stream.write(data)
                data = wf.readframes(self.buffer_size)
            
            stream.stop_stream()
            stream.close()
    
    def play_audio_data(
        self, 
        audio_data: bytes, 
        sample_rate: int = config.AUDIO_SAMPLE_RATE,
        channels: int = config.AUDIO_CHANNELS,
        sample_width: int = config.AUDIO_FORMAT_WIDTH
    ) -> None:
        """Play raw audio data directly."""
        stream = self.audio.open(
            format=self.audio.get_format_from_width(sample_width),
            channels=channels,
            rate=sample_rate,
            output=True,
            frames_per_buffer=self.buffer_size
        )
        
        # Play in chunks for smoother output
        offset = 0
        chunk_bytes = self.buffer_size * sample_width * channels
        
        while offset < len(audio_data):
            chunk = audio_data[offset:offset + chunk_bytes]
            stream.write(chunk)
            offset += chunk_bytes
        
        stream.stop_stream()
        stream.close()
    
    def cleanup(self) -> None:
        """Clean up audio resources."""
        try:
            self.audio.terminate()
        except:
            pass
    
    def __del__(self):
        self.cleanup()


if __name__ == "__main__":
    # Test recording
    recorder = AudioRecorder()
    test_file = recorder.test_recording(3)
    
    # Test playback
    print("Playing back recording...")
    player = AudioPlayer()
    player.play_wav(test_file)
    print("Done!")
