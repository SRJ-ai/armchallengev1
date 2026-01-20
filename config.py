"""
Configuration settings for the Hindi Voice Assistant.
"""
import os

# ============================================================================
# AUDIO CONFIGURATION
# ============================================================================
AUDIO_SAMPLE_RATE = 16000  # 16kHz for Vosk compatibility
AUDIO_CHANNELS = 1         # Mono audio
AUDIO_CHUNK_SIZE = 1600    # 100ms chunks for lower latency (was 4000)
AUDIO_FORMAT_WIDTH = 2     # 16-bit audio (2 bytes)
AUDIO_BUFFER_SIZE = 4096   # Larger buffer for smoother playback

# ============================================================================
# MODEL PATHS
# ============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
VOSK_MODEL_PATH = os.path.join(MODEL_DIR, "vosk-model-small-hi-0.22")

# ============================================================================
# TTS CONFIGURATION
# ============================================================================
TTS_VOICE = "hi"           # Hindi voice for eSpeak-NG
TTS_SPEED = 100            # Words per minute (much slower for clarity)
TTS_PITCH = 40             # Lower pitch for clearer sound
TTS_AMPLITUDE = 80         # Lower volume reduces noise/distortion
TTS_GAP = 15               # Word gap 150ms for clear separation

# ============================================================================
# ASSISTANT CONFIGURATION
# ============================================================================
WAKE_WORDS = ["सुनो", "हेलो", "ओके"]  # Wake words to activate assistant
SILENCE_TIMEOUT = 1.2       # Reduced silence timeout for faster response (was 2.0)
LISTEN_TIMEOUT = 10.0       # Max seconds to listen for command

# ============================================================================
# HINDI COMMANDS MAPPING
# Intent: (keywords, response_template)
# ============================================================================
COMMANDS = {
    "greeting": {
        "keywords": [
            "नमस्ते", "नमस्कार", "हेलो", "हाय", "हैलो", "हेल्लो",
            "namaste", "namaskar", "hello", "hi", "hey",
            "सुप्रभात", "शुभ", "राम राम", "हेलू", "नमस्ता"
        ],
        "response": "नमस्ते! मैं आपकी कैसे मदद कर सकता हूं?"
    },
    "get_time": {
        "keywords": [
            # Hindi variations
            "समय", "टाइम", "बजे", "बज", "वक्त", "वक़्त",
            # Vosk common outputs
            "समाई", "समै", "सामय", "समे",
            # Phrases
            "क्या बजा", "कितने बजे", "कितना बजा", "कितने बज",
            "समय क्या", "टाइम क्या", "समय बताओ", "टाइम बताओ",
            # Transliterated
            "time", "samay", "kitne baje", "kya baja", "waqt"
        ],
        "response": "अभी {time} बज रहे हैं।"
    },
    "get_date": {
        "keywords": [
            "तारीख", "तारिख", "डेट", "दिनांक",
            "आज की तारीख", "कौन सी तारीख", "तारीख बताओ",
            "date", "tareekh", "tarikh", "aaj ki tarikh",
            # Vosk variations
            "तारीक", "तारिक"
        ],
        "response": "आज की तारीख {date} है।"
    },
    "get_day": {
        "keywords": [
            "दिन", "वार", "आज",
            "कौन सा दिन", "क्या दिन", "आज का दिन", "आज क्या दिन",
            "दिन बताओ", "आज कौन सा",
            "day", "din", "kaun sa din", "aaj ka din",
            # Day names (if user asks about specific day)
            "सोमवार", "मंगलवार", "बुधवार", "गुरुवार", 
            "शुक्रवार", "शनिवार", "रविवार"
        ],
        "response": "आज {day} है।"
    },
    "get_weather": {
        "keywords": [
            "मौसम", "वेदर", "तापमान", "गर्मी", "सर्दी", "बारिश",
            "weather", "mausam", "temperature", "garmi", "sardi", "barish",
            "कैसा मौसम", "मौसम कैसा", "मौसम बताओ",
            # Vosk variations
            "मोसम", "मौषम"
        ],
        "response": "मौसम साफ है, तापमान लगभग 25 डिग्री सेल्सियस है।"
    },
    "thanks": {
        "keywords": [
            "धन्यवाद", "शुक्रिया", "थैंक्स", "थैंक यू", "धन्यवाद जी",
            "thanks", "thank you", "dhanyavaad", "shukriya", "meharbani",
            # Vosk variations
            "धन्यवात", "थैंक", "शुक्रीया"
        ],
        "response": "आपका स्वागत है!"
    },
    "goodbye": {
        "keywords": [
            "अलविदा", "बाय", "बाय बाय", "फिर मिलेंगे", "चलता हूं", "जाता हूं",
            "bye", "bye bye", "goodbye", "alvida", "phir milenge", "tata",
            "चलो", "जाओ", "बंद करो"
        ],
        "response": "अलविदा! अपना ख्याल रखें।"
    },
    "help": {
        "keywords": [
            # Direct help words
            "मदद", "हेल्प", "सहायता",
            # What can you do phrases - IMPORTANT for "क्या कर सकते हैं"
            "क्या कर सकते", "क्या कर सकता", "क्या कर सकती",
            "तुम क्या कर सकते", "आप क्या कर सकते",
            "क्या क्या कर सकते", "कर सकते हो", "कर सकता है",
            # Other help phrases
            "बताओ क्या", "क्या बता सकते", "कैसे मदद",
            "help", "madad", "sahayata", "kya kar sakte"
        ],
        "response": "मैं आपको समय, तारीख, दिन, और मौसम बता सकता हूं। बस पूछिए!"
    },
    "set_timer": {
        "keywords": [
            "टाइमर", "अलार्म", "याद दिला", "रिमाइंडर",
            "timer", "alarm", "reminder", "yaad dila",
            "टाइमर लगाओ", "अलार्म लगाओ"
        ],
        "response": "टाइमर सेट हो गया।"
    },
    "stop": {
        "keywords": [
            "रुको", "बंद", "बंद करो", "रुक जाओ", "चुप", "बस", "रुक",
            "stop", "ruko", "band", "band karo", "bas", "chup",
            "रुकिए", "बस करो"
        ],
        "response": "ठीक है, रुक गया।"
    },
    "repeat": {
        "keywords": [
            "दोहराओ", "फिर से", "फिर से बोलो", "दोबारा", "रिपीट",
            "repeat", "dohrao", "phir se", "dobara", "ek baar aur",
            "फिर बोलो", "दुबारा"
        ],
        "response": None  # Will repeat last response
    },
    "battery": {
        "keywords": [
            "बैटरी", "चार्ज", "पावर", "कितनी बैटरी",
            "battery", "charge", "power", "kitni battery",
            "बैटरी कितनी", "चार्जिंग"
        ],
        "response": "बैटरी {battery}% चार्ज है।"
    },
    "volume_up": {
        "keywords": [
            # Standard
            "वॉल्यूम बढ़ाओ", "आवाज बढ़ाओ", "आवाज ज्यादा", "जोर से",
            # Vosk ASR variations (बड़ा instead of बढ़ा)
            "वॉल्यूम बड़ा", "वॉल्यूम बड़ा हुआ", "वॉल्यूम बड़ी",
            "आवाज बड़ा", "आवाज बड़ी", "आवाज बड़ी करो",
            # Other variations
            "volume up", "louder", "volume badhao", "awaaz badhao",
            "आवाज़ बढ़ाओ", "वॉल्यूम ऊपर", "आवाज़ बड़ा"
        ],
        "response": "वॉल्यूम बढ़ा दिया।"
    },
    "volume_down": {
        "keywords": [
            "वॉल्यूम कम", "आवाज कम", "धीरे", "धीमा",
            "volume down", "quieter", "volume kam", "awaaz kam", "softer",
            "आवाज़ कम", "वॉल्यूम नीचे"
        ],
        "response": "वॉल्यूम कम कर दिया।"
    },
    "unknown": {
        "keywords": [],
        "response": "माफ कीजिए, मैं समझ नहीं पाया। कृपया फिर से कहें।"
    }
}

# Hindi day names
HINDI_DAYS = {
    "Monday": "सोमवार",
    "Tuesday": "मंगलवार", 
    "Wednesday": "बुधवार",
    "Thursday": "गुरुवार",
    "Friday": "शुक्रवार",
    "Saturday": "शनिवार",
    "Sunday": "रविवार"
}

# Hindi month names
HINDI_MONTHS = {
    1: "जनवरी", 2: "फरवरी", 3: "मार्च", 4: "अप्रैल",
    5: "मई", 6: "जून", 7: "जुलाई", 8: "अगस्त",
    9: "सितंबर", 10: "अक्टूबर", 11: "नवंबर", 12: "दिसंबर"
}
