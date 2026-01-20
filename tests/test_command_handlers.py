"""
Unit tests for the Command Handlers module.
"""
import pytest
import sys
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from command_handlers import CommandHandlers
import config


class TestCommandHandlers:
    """Test cases for CommandHandlers class."""
    
    @pytest.fixture
    def handlers(self):
        """Create a fresh handlers instance for each test."""
        return CommandHandlers()
    
    # --- Greeting Tests ---
    
    def test_greeting_response(self, handlers):
        """Test greeting returns expected response."""
        response = handlers.handle("greeting", {})
        assert response == config.COMMANDS["greeting"]["response"]
        assert "नमस्ते" in response
    
    # --- Time Tests ---
    
    def test_get_time_contains_time(self, handlers):
        """Test time response contains time components."""
        response = handlers.handle("get_time", {})
        assert "बज" in response  # Contains "baj" (o'clock in Hindi)
    
    def test_get_time_period(self, handlers):
        """Test time response contains period (morning/evening)."""
        response = handlers.handle("get_time", {})
        assert "सुबह" in response or "शाम" in response
    
    # --- Date Tests ---
    
    def test_get_date_contains_year(self, handlers):
        """Test date response contains current year."""
        response = handlers.handle("get_date", {})
        current_year = str(datetime.now().year)
        assert current_year in response
    
    def test_get_date_contains_month(self, handlers):
        """Test date response contains Hindi month name."""
        response = handlers.handle("get_date", {})
        current_month = datetime.now().month
        hindi_month = config.HINDI_MONTHS[current_month]
        assert hindi_month in response
    
    # --- Day Tests ---
    
    def test_get_day_contains_hindi_day(self, handlers):
        """Test day response contains Hindi day name."""
        response = handlers.handle("get_day", {})
        # Check that one of the Hindi day names is in the response
        hindi_days = list(config.HINDI_DAYS.values())
        assert any(day in response for day in hindi_days)
    
    # --- Weather Tests ---
    
    def test_get_weather_response(self, handlers):
        """Test weather returns static response."""
        response = handlers.handle("get_weather", {})
        assert response == config.COMMANDS["get_weather"]["response"]
    
    # --- Thanks Tests ---
    
    def test_thanks_response(self, handlers):
        """Test thanks returns expected response."""
        response = handlers.handle("thanks", {})
        assert response == config.COMMANDS["thanks"]["response"]
    
    # --- Goodbye Tests ---
    
    def test_goodbye_response(self, handlers):
        """Test goodbye returns expected response."""
        response = handlers.handle("goodbye", {})
        assert "अलविदा" in response
    
    # --- Help Tests ---
    
    def test_help_response(self, handlers):
        """Test help returns expected response."""
        response = handlers.handle("help", {})
        assert response == config.COMMANDS["help"]["response"]
    
    # --- Timer Tests ---
    
    def test_timer_default_duration(self, handlers):
        """Test timer with no duration uses default."""
        response = handlers.handle("set_timer", {})
        assert "60" in response or "सेकंड" in response
    
    def test_timer_custom_duration(self, handlers):
        """Test timer with custom duration."""
        response = handlers.handle("set_timer", {"duration": 30})
        assert "30" in response
    
    def test_timer_sets_flag(self, handlers):
        """Test timer sets active flag."""
        handlers.handle("set_timer", {})
        assert handlers.timer_active is True
    
    # --- Stop Tests ---
    
    def test_stop_response(self, handlers):
        """Test stop returns expected response."""
        response = handlers.handle("stop", {})
        assert response == config.COMMANDS["stop"]["response"]
    
    def test_stop_clears_timer(self, handlers):
        """Test stop clears timer flag."""
        handlers.timer_active = True
        handlers.handle("stop", {})
        assert handlers.timer_active is False
    
    # --- Repeat Tests ---
    
    def test_repeat_returns_last_response(self, handlers):
        """Test repeat returns the last response."""
        # First command
        handlers.handle("greeting", {})
        
        # Repeat
        response = handlers.handle("repeat", {})
        assert response == config.COMMANDS["greeting"]["response"]
    
    def test_repeat_no_previous(self, handlers):
        """Test repeat with no previous response."""
        response = handlers.handle("repeat", {})
        assert "पिछला" in response  # "previous" in Hindi
    
    # --- Battery Tests ---
    
    def test_battery_response_format(self, handlers):
        """Test battery response contains percentage."""
        response = handlers.handle("battery", {})
        assert "%" in response
    
    # --- Volume Tests ---
    
    @patch('command_handlers.subprocess.run')
    def test_volume_up_calls_amixer(self, mock_run, handlers):
        """Test volume up calls amixer."""
        handlers.handle("volume_up", {})
        mock_run.assert_called()
    
    @patch('command_handlers.subprocess.run')
    def test_volume_down_calls_amixer(self, mock_run, handlers):
        """Test volume down calls amixer."""
        handlers.handle("volume_down", {})
        mock_run.assert_called()
    
    # --- Unknown Tests ---
    
    def test_unknown_response(self, handlers):
        """Test unknown returns expected response."""
        response = handlers.handle("unknown", {})
        assert response == config.COMMANDS["unknown"]["response"]
    
    def test_invalid_intent(self, handlers):
        """Test invalid intent returns unknown response."""
        response = handlers.handle("invalid_intent_xyz", {})
        assert response == config.COMMANDS["unknown"]["response"]


class TestLastResponseTracking:
    """Test last response tracking behavior."""
    
    def test_last_response_updated(self):
        """Test last response is updated after commands."""
        handlers = CommandHandlers()
        
        handlers.handle("greeting", {})
        assert handlers.last_response == config.COMMANDS["greeting"]["response"]
    
    def test_last_response_not_updated_by_repeat(self):
        """Test repeat doesn't update last response."""
        handlers = CommandHandlers()
        
        handlers.handle("greeting", {})
        original = handlers.last_response
        
        handlers.handle("repeat", {})
        assert handlers.last_response == original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
