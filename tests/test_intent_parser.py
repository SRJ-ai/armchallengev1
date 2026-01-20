"""
Unit tests for the Intent Parser module.
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from intent_parser import IntentParser


class TestIntentParser:
    """Test cases for IntentParser class."""
    
    @pytest.fixture
    def parser(self):
        """Create a fresh parser instance for each test."""
        return IntentParser()
    
    # --- Greeting Tests ---
    
    def test_greeting_namaste(self, parser):
        """Test Hindi greeting recognition."""
        intent, params = parser.parse("नमस्ते")
        assert intent == "greeting"
    
    def test_greeting_hello(self, parser):
        """Test transliterated greeting."""
        intent, params = parser.parse("hello")
        assert intent == "greeting"
    
    # --- Time Tests ---
    
    def test_get_time_hindi(self, parser):
        """Test Hindi time query."""
        intent, params = parser.parse("समय क्या है")
        assert intent == "get_time"
    
    def test_get_time_partial(self, parser):
        """Test partial time query."""
        intent, params = parser.parse("अभी कितने बजे हैं")
        assert intent == "get_time"
    
    # --- Date Tests ---
    
    def test_get_date_hindi(self, parser):
        """Test Hindi date query."""
        intent, params = parser.parse("आज की तारीख क्या है")
        assert intent == "get_date"
    
    def test_get_date_transliterated(self, parser):
        """Test transliterated date query."""
        intent, params = parser.parse("aaj ki tareekh")
        assert intent == "get_date"
    
    # --- Day Tests ---
    
    def test_get_day_hindi(self, parser):
        """Test Hindi day query."""
        intent, params = parser.parse("आज कौन सा दिन है")
        assert intent == "get_day"
    
    # --- Weather Tests ---
    
    def test_get_weather_hindi(self, parser):
        """Test Hindi weather query."""
        intent, params = parser.parse("मौसम कैसा है")
        assert intent == "get_weather"
    
    def test_get_weather_transliterated(self, parser):
        """Test transliterated weather query."""
        intent, params = parser.parse("mausam kaisa hai")
        assert intent == "get_weather"
    
    # --- Thanks Tests ---
    
    def test_thanks_hindi(self, parser):
        """Test Hindi thanks."""
        intent, params = parser.parse("धन्यवाद")
        assert intent == "thanks"
    
    def test_thanks_shukriya(self, parser):
        """Test alternative thanks."""
        intent, params = parser.parse("शुक्रिया")
        assert intent == "thanks"
    
    # --- Goodbye Tests ---
    
    def test_goodbye_hindi(self, parser):
        """Test Hindi goodbye."""
        intent, params = parser.parse("अलविदा")
        assert intent == "goodbye"
    
    def test_goodbye_bye(self, parser):
        """Test English goodbye."""
        intent, params = parser.parse("bye")
        assert intent == "goodbye"
    
    # --- Help Tests ---
    
    def test_help_hindi(self, parser):
        """Test Hindi help request."""
        intent, params = parser.parse("मदद करो")
        assert intent == "help"
    
    # --- Timer Tests ---
    
    def test_timer_basic(self, parser):
        """Test timer command."""
        intent, params = parser.parse("टाइमर लगाओ")
        assert intent == "set_timer"
    
    def test_timer_with_duration(self, parser):
        """Test timer with duration."""
        intent, params = parser.parse("5 मिनट का टाइमर लगाओ")
        assert intent == "set_timer"
        assert params.get("duration") == 5
    
    # --- Stop Tests ---
    
    def test_stop_ruko(self, parser):
        """Test stop command."""
        intent, params = parser.parse("रुको")
        assert intent == "stop"
    
    def test_stop_band(self, parser):
        """Test alternative stop."""
        intent, params = parser.parse("बंद करो")
        assert intent == "stop"
    
    # --- Repeat Tests ---
    
    def test_repeat_dohrao(self, parser):
        """Test repeat command."""
        # First make a command to have something to repeat
        parser.parse("नमस्ते")
        
        intent, params = parser.parse("दोहराओ")
        assert intent == "repeat"
        assert params.get("last_intent") == "greeting"
    
    # --- Battery Tests ---
    
    def test_battery_hindi(self, parser):
        """Test battery query."""
        intent, params = parser.parse("बैटरी कितनी है")
        assert intent == "battery"
    
    # --- Volume Tests ---
    
    def test_volume_up(self, parser):
        """Test volume up command."""
        intent, params = parser.parse("वॉल्यूम बढ़ाओ")
        assert intent == "volume_up"
    
    def test_volume_down(self, parser):
        """Test volume down command."""
        intent, params = parser.parse("वॉल्यूम कम करो")
        assert intent == "volume_down"
    
    # --- Unknown Tests ---
    
    def test_unknown_empty(self, parser):
        """Test empty input."""
        intent, params = parser.parse("")
        assert intent == "unknown"
    
    def test_unknown_gibberish(self, parser):
        """Test unrecognized input."""
        intent, params = parser.parse("xyzabc random text")
        assert intent == "unknown"
    
    def test_unknown_whitespace(self, parser):
        """Test whitespace only."""
        intent, params = parser.parse("   ")
        assert intent == "unknown"
    
    # --- Normalization Tests ---
    
    def test_case_insensitive(self, parser):
        """Test case insensitivity."""
        intent1, _ = parser.parse("HELLO")
        intent2, _ = parser.parse("hello")
        assert intent1 == intent2 == "greeting"
    
    def test_whitespace_handling(self, parser):
        """Test whitespace handling."""
        intent, _ = parser.parse("  समय क्या है  ")
        assert intent == "get_time"


class TestIntentParserState:
    """Test stateful behavior of IntentParser."""
    
    def test_last_intent_tracking(self):
        """Test that last intent is tracked correctly."""
        parser = IntentParser()
        
        parser.parse("नमस्ते")
        assert parser.last_intent == "greeting"
        
        parser.parse("समय क्या है")
        assert parser.last_intent == "get_time"
    
    def test_repeat_uses_last_intent(self):
        """Test that repeat command returns last intent."""
        parser = IntentParser()
        
        parser.parse("मौसम कैसा है")
        intent, params = parser.parse("दोहराओ")
        
        assert intent == "repeat"
        assert params["last_intent"] == "get_weather"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
