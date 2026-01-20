# 🎤 Offline Hindi Voice Assistant

An offline, privacy-preserving voice assistant for Raspberry Pi that processes Hindi voice commands entirely on-device using Vosk ASR and eSpeak-NG TTS.

## ✨ Features

- **100% Offline** - No cloud dependencies, all processing on-device
- **Hindi Support** - Native Hindi speech recognition and text-to-speech
- **Low Latency** - Sub-2-second response time
- **Privacy-First** - Your voice data never leaves your device
- **14 Commands** - Time, date, weather, volume control, and more

## 📋 Requirements

### Hardware
- Raspberry Pi 4 (or similar Arm SBC)
- USB microphone
- Speaker (3.5mm jack or HDMI audio)

### Software
- Raspberry Pi OS / Debian / Ubuntu
- Python 3.8+

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <repo-url>
cd armchallenge
chmod +x setup.sh
./setup.sh
```

### 2. Activate Environment
```bash
source venv/bin/activate
```

### 3. Run the Assistant
```bash
python run.py
```

## 🗣️ Supported Commands

| Hindi Command | English Meaning | Response |
|--------------|-----------------|----------|
| नमस्ते | Hello | Greeting |
| समय क्या है | What time is it? | Current time |
| आज की तारीख | Today's date | Current date |
| कौन सा दिन है | What day is it? | Day of week |
| मौसम कैसा है | How's the weather? | Weather info |
| धन्यवाद | Thank you | You're welcome |
| अलविदा | Goodbye | Farewell |
| मदद करो | Help | Command list |
| टाइमर लगाओ | Set timer | Timer started |
| रुको | Stop | Stops action |
| दोहराओ | Repeat | Repeats last |
| बैटरी कितनी है | Battery level? | Battery status |
| वॉल्यूम बढ़ाओ | Volume up | Increases volume |
| वॉल्यूम कम करो | Volume down | Decreases volume |

## 🔧 Usage Options

```bash
# Continuous listening mode (default)
python run.py

# Single command mode
python run.py --single

# Test TTS
python run.py --test-tts "नमस्ते, कैसे हैं?"

# Test ASR (5-second recording)
python run.py --test-asr
```

## 📁 Project Structure

```
armchallenge/
├── run.py              # Entry point
├── assistant.py        # Main assistant class
├── asr_engine.py       # Vosk speech recognition
├── tts_engine.py       # eSpeak-NG text-to-speech
├── intent_parser.py    # Command intent matching
├── command_handlers.py # Command execution logic
├── audio_io.py         # Microphone/speaker handling
├── config.py           # Configuration & commands
├── setup.sh            # Installation script
├── requirements.txt    # Python dependencies
├── models/             # Vosk Hindi model
│   └── vosk-model-small-hi-0.22/
├── tests/              # Unit tests
└── docs/               # Documentation
```

## 🏗️ Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Microphone  │───▶│   PyAudio    │───▶│  Vosk ASR    │
│    (USB)     │    │   Recorder   │    │  (Hindi)     │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                                │
                                                ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Speaker    │◀───│  eSpeak-NG   │◀───│   Intent     │
│  (3.5mm)     │    │   (Hindi)    │    │   Parser     │
└──────────────┘    └──────────────┘    └──────────────┘
```

## ⚡ Performance

| Metric | Target | Typical |
|--------|--------|---------|
| Response Time | < 2s | ~1.2s |
| ASR Accuracy | > 85% | 90%+ |
| Model Size | < 100MB | 48MB |
| RAM Usage | < 500MB | ~300MB |

## 🔍 Troubleshooting

### No audio input
```bash
# List audio devices
arecord -l

# Test microphone
arecord -d 3 test.wav && aplay test.wav
```

### No audio output
```bash
# Test speaker
espeak-ng -v hi "नमस्ते"

# Check ALSA
alsamixer
```

### Model not found
```bash
# Re-download model
./setup.sh
```

## 📖 Documentation

- [Architecture Details](docs/ARCHITECTURE.md)
- [Performance Tuning](docs/PERFORMANCE.md)
- [Hindi ASR/TTS Notes](docs/HINDI_NOTES.md)

## 📜 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- [Vosk](https://alphacephei.com/vosk/) - Offline speech recognition
- [eSpeak-NG](https://github.com/espeak-ng/espeak-ng) - Text-to-speech
- [PyAudio](https://pypi.org/project/PyAudio/) - Audio I/O
