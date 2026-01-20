"""
Main Voice Assistant module.
Integrates ASR, intent parsing, command handling, and TTS into a complete pipeline.
"""
import time
import signal
import sys
from typing import Optional
import config
from audio_io import AudioRecorder
from asr_engine import ASREngine
from intent_parser import IntentParser
from tts_engine import TTSEngine
from command_handlers import CommandHandlers


class VoiceAssistant:
    """
    Offline Hindi Voice Assistant.
    
    Provides a complete voice interaction pipeline:
    Microphone → ASR → Intent Parser → Command Handler → TTS → Speaker
    """
    
    def __init__(self):
        """Initialize all components of the voice assistant."""
        print("=" * 60)
        print("   Offline Hindi Voice Assistant")
        print("   ऑफलाइन हिंदी वॉइस असिस्टेंट")
        print("=" * 60)
        print()
        
        print("Initializing components...")
        
        # Initialize audio
        print("  [1/5] Audio recorder...")
        self.audio = AudioRecorder()
        
        # Initialize ASR
        print("  [2/5] Speech recognition (Vosk)...")
        self.asr = ASREngine()
        
        # Initialize intent parser
        print("  [3/5] Intent parser...")
        self.parser = IntentParser()
        
        # Initialize TTS
        print("  [4/5] Text-to-speech (eSpeak-NG)...")
        self.tts = TTSEngine()
        
        # Initialize command handlers
        print("  [5/5] Command handlers...")
        self.handlers = CommandHandlers()
        
        # State
        self.running = False
        self.listening = False
        
        print()
        print("✓ All components initialized successfully!")
        print()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print("\n\nShutting down...")
        self.stop()
        sys.exit(0)
    
    def speak(self, text: str) -> None:
        """Speak a response using TTS."""
        if text:
            print(f"🔊 Speaking: {text}")
            self.tts.speak(text)
    
    def process_command(self, text: str) -> Optional[str]:
        """
        Process recognized text through the pipeline.
        
        Args:
            text: Transcribed text from ASR
            
        Returns:
            Response text or None
        """
        if not text or not text.strip():
            return None
        
        print(f"📝 Recognized: {text}")
        
        # Parse intent
        intent, params = self.parser.parse(text)
        print(f"🎯 Intent: {intent}, Params: {params}")
        
        # Handle command
        response = self.handlers.handle(intent, params)
        
        return response
    
    def listen_and_respond(self) -> bool:
        """
        Listen for a command and respond with optimized latency.
        
        Returns:
            True if should continue, False if goodbye
        """
        print("\n🎤 Listening... (speak in Hindi)")
        
        # Optimized audio collection with voice activity detection
        frames = []
        silence_count = 0
        speech_detected = False
        start_time = time.time()
        min_speech_frames = 3  # Minimum frames to consider valid speech
        
        self.audio.start_stream()
        
        try:
            while True:
                # Check timeout (faster check)
                elapsed = time.time() - start_time
                if elapsed > config.LISTEN_TIMEOUT:
                    print("   (timeout)")
                    break
                
                # Read audio chunk
                chunk = self.audio.read_chunk()
                
                # Check for speech using adaptive threshold
                is_speech = self.audio.is_speech(chunk)
                
                if is_speech:
                    speech_detected = True
                    silence_count = 0
                    frames.append(chunk)
                elif speech_detected:
                    frames.append(chunk)
                    silence_count += 1
                    
                    # Calculate silence duration based on chunk size
                    # Each chunk is AUDIO_CHUNK_SIZE samples at AUDIO_SAMPLE_RATE
                    chunk_duration = config.AUDIO_CHUNK_SIZE / config.AUDIO_SAMPLE_RATE
                    silence_duration = silence_count * chunk_duration
                    
                    # Early exit on silence (optimized timeout)
                    if silence_duration > config.SILENCE_TIMEOUT:
                        break
        
        finally:
            self.audio.stop_stream()
        
        # Filter out noise-only captures
        if not speech_detected or len(frames) < min_speech_frames:
            return True
        
        # Transcribe audio
        audio_data = b''.join(frames)
        print("⏳ Processing...")
        
        # Measure latency
        process_start = time.time()
        
        text = self.asr.transcribe_audio(audio_data)
        
        asr_time = time.time() - process_start
        
        if text:
            response = self.process_command(text)
            
            if response:
                self.speak(response)
                
                # Log detailed latency
                total_latency = time.time() - process_start
                print(f"⏱️  ASR: {asr_time:.2f}s | Total: {total_latency:.2f}s")
            
            # Check if user said goodbye
            intent, _ = self.parser.parse(text)
            if intent == "goodbye":
                return False
        else:
            print("   (no speech detected)")
        
        return True
    
    def run_continuous(self) -> None:
        """Run the assistant in continuous listening mode."""
        self.running = True
        
        # Welcome message
        welcome = "नमस्ते! मैं आपका हिंदी वॉइस असिस्टेंट हूं। आप मुझसे समय, तारीख, या मौसम पूछ सकते हैं।"
        self.speak(welcome)
        
        print("\n" + "=" * 60)
        print("Ready! Say commands in Hindi.")
        print("Press Ctrl+C to exit.")
        print("=" * 60)
        
        while self.running:
            try:
                should_continue = self.listen_and_respond()
                if not should_continue:
                    self.running = False
                    break
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                continue
        
        self.stop()
    
    def run_single(self) -> str:
        """
        Run single command mode - listen once and respond.
        
        Returns:
            The response text
        """
        print("\n🎤 Listening for command...")
        
        # Collect audio
        audio_data = self.audio.record_audio(5)  # 5 second recording
        
        # Transcribe
        text = self.asr.transcribe_audio(audio_data)
        
        if not text:
            return "कोई आवाज नहीं सुनाई दी।"
        
        # Process and respond
        response = self.process_command(text)
        
        if response:
            self.speak(response)
        
        return response or ""
    
    def stop(self) -> None:
        """Stop the assistant and clean up resources."""
        self.running = False
        self.audio.cleanup()
        print("\n👋 Assistant stopped. अलविदा!")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Offline Hindi Voice Assistant"
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="Run in single command mode (listen once, respond, exit)"
    )
    parser.add_argument(
        "--test-tts",
        type=str,
        help="Test TTS with the given text"
    )
    parser.add_argument(
        "--test-asr",
        action="store_true",
        help="Test ASR with a 5-second recording"
    )
    
    args = parser.parse_args()
    
    if args.test_tts:
        tts = TTSEngine()
        tts.speak(args.test_tts)
        return
    
    if args.test_asr:
        print("Recording for 5 seconds...")
        audio = AudioRecorder()
        data = audio.record_audio(5)
        audio.cleanup()
        
        print("Transcribing...")
        asr = ASREngine()
        text = asr.transcribe_audio(data)
        print(f"Result: {text}")
        return
    
    # Run assistant
    assistant = VoiceAssistant()
    
    if args.single:
        assistant.run_single()
    else:
        assistant.run_continuous()


if __name__ == "__main__":
    main()
