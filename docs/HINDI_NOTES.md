# Hindi ASR/TTS Challenges and Solutions

## Challenges in Hindi Speech Processing

### 1. Script Complexity

Hindi uses the Devanagari script with:
- 11 vowels (स्वर)
- 33 consonants (व्यंजन)
- Conjunct consonants (संयुक्त व्यंजन)
- Nasalization marks (anusvara, chandrabindu)

This creates challenges for both ASR acoustic modeling and TTS grapheme-to-phoneme conversion.

### 2. Dialectal Variations

Hindi has significant regional variations:
- Khariboli (standard Hindi)
- Braj Bhasha
- Awadhi
- Bhojpuri

The Vosk Hindi model is primarily trained on standard Hindi (Khariboli).

### 3. Code-Mixing

Indian speakers frequently mix Hindi with English (Hinglish):
- "Time kya hai?" instead of "समय क्या है?"
- "Volume badhao" instead of "आवाज़ बढ़ाओ"

Our intent parser handles both pure Hindi and transliterated/mixed inputs.

## Vosk Hindi Model Details

### Model Architecture
- **Acoustic Model**: Time-Delay Neural Network (TDNN)
- **Language Model**: 3-gram with pruning
- **Vocabulary**: ~100,000 words
- **Training Data**: Common Voice, OpenSLR, private datasets

### Optimization for Raspberry Pi
```
Model: vosk-model-small-hi-0.22
Size: 48 MB (compressed from ~200 MB full model)
Quantization: 8-bit integer
Beam Width: Reduced for speed
```

### Recognition Accuracy

| Condition | WER (Word Error Rate) |
|-----------|----------------------|
| Clean speech | 15-20% |
| Background noise | 25-35% |
| Code-mixed | 20-30% |

## eSpeak-NG Hindi Voice

### Characteristics
- **Method**: Formant synthesis
- **Quality**: Robotic but intelligible
- **Advantages**: Tiny footprint, fast synthesis

### Configuration
```bash
# Default Hindi voice
espeak-ng -v hi "नमस्ते"

# Slower, clearer speech
espeak-ng -v hi -s 120 "नमस्ते"

# Different pitch
espeak-ng -v hi -p 75 "नमस्ते"
```

### Known Limitations
1. Unnatural prosody
2. Limited emotional expression
3. Proper noun pronunciation may be incorrect
4. Some conjunct consonants mispronounced

## Recommendations

### Improving ASR Accuracy

1. **Use larger model** when memory allows:
   ```bash
   # Download full model (~200MB)
   wget https://alphacephei.com/vosk/models/vosk-model-hi-0.22.zip
   ```

2. **Add domain-specific language model** for your commands

3. **Implement keyword spotting** for wake words

### Improving TTS Quality

1. **Consider Piper TTS** for neural synthesis:
   - Better quality
   - ~100MB model
   - Requires more RAM

2. **Pre-generate common responses** as WAV files:
   ```python
   # Generate at setup time
   espeak-ng -w greeting.wav -v hi "नमस्ते, मैं आपकी कैसे मदद कर सकता हूं?"
   ```

3. **Use Speech Rate and Pitch** tuning:
   ```python
   # Slower, more understandable
   TTS_SPEED = 130
   TTS_PITCH = 60
   ```

## Performance Tuning Tips

1. **Reduce chunk size** for faster perceived response:
   ```python
   AUDIO_CHUNK_SIZE = 2000  # 125ms chunks
   ```

2. **Lower VAD threshold** for noisy environments:
   ```python
   threshold=200  # More sensitive
   ```

3. **Pre-warm the ASR model** at startup:
   ```python
   # Process dummy audio to load model into cache
   asr.transcribe_audio(b'\x00' * 32000)
   ```
