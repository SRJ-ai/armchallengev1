#!/bin/bash
# Setup script for the Hindi Voice Assistant
# Run this on your Raspberry Pi or Linux system

set -e

echo "=============================================="
echo "  Hindi Voice Assistant Setup"
echo "  हिंदी वॉइस असिस्टेंट सेटअप"
echo "=============================================="
echo

# Check if running as root for system packages
if [ "$EUID" -eq 0 ]; then
    APT_CMD="apt-get"
else
    APT_CMD="sudo apt-get"
fi

# --- System Dependencies ---
echo "[1/5] Installing system dependencies..."
$APT_CMD update
$APT_CMD install -y \
    espeak-ng \
    portaudio19-dev \
    python3-dev \
    python3-pip \
    python3-venv \
    alsa-utils \
    libatlas-base-dev

echo "✓ System dependencies installed"
echo

# --- Create virtual environment ---
echo "[2/5] Creating Python virtual environment..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

echo "✓ Virtual environment created at $VENV_DIR"
echo

# --- Install Python packages ---
echo "[3/5] Installing Python packages..."
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"

echo "✓ Python packages installed"
echo

# --- Download Vosk Hindi Model ---
echo "[4/5] Downloading Vosk Hindi model..."
MODEL_DIR="$SCRIPT_DIR/models"
MODEL_NAME="vosk-model-small-hi-0.22"
MODEL_URL="https://alphacephei.com/vosk/models/$MODEL_NAME.zip"
MODEL_PATH="$MODEL_DIR/$MODEL_NAME"

mkdir -p "$MODEL_DIR"

if [ ! -d "$MODEL_PATH" ]; then
    echo "  Downloading from: $MODEL_URL"
    wget -q --show-progress -O "$MODEL_DIR/$MODEL_NAME.zip" "$MODEL_URL"
    
    echo "  Extracting model..."
    unzip -q "$MODEL_DIR/$MODEL_NAME.zip" -d "$MODEL_DIR"
    rm "$MODEL_DIR/$MODEL_NAME.zip"
    
    echo "✓ Hindi model downloaded to: $MODEL_PATH"
else
    echo "✓ Hindi model already exists at: $MODEL_PATH"
fi
echo

# --- Verify Installation ---
echo "[5/5] Verifying installation..."

# Test eSpeak-NG
echo -n "  eSpeak-NG: "
if command -v espeak-ng &> /dev/null; then
    echo "OK"
else
    echo "FAILED"
    exit 1
fi

# Test Python packages
echo -n "  Python packages: "
python3 -c "import vosk; import pyaudio; print('OK')"

# Test Hindi model
echo -n "  Hindi model: "
if [ -d "$MODEL_PATH" ]; then
    echo "OK"
else
    echo "FAILED - Model not found"
    exit 1
fi

echo
echo "=============================================="
echo "  Setup Complete! / सेटअप पूर्ण!"
echo "=============================================="
echo
echo "To run the assistant:"
echo "  source venv/bin/activate"
echo "  python run.py"
echo
echo "Or in single-command mode:"
echo "  python run.py --single"
echo
echo "Test TTS:"
echo "  python run.py --test-tts 'नमस्ते, कैसे हैं आप?'"
echo
echo "Test ASR:"
echo "  python run.py --test-asr"
echo
