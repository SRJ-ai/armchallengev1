"""
Command Handlers for the Hindi Voice Assistant.
Implements the business logic for each supported command.
"""
import datetime
from typing import Dict, Any, Optional, Callable
from settings import settings
from logger import get_logger
from system_control import SystemControl

logger = get_logger("command_handlers")

class CommandHandlers:
    """Handles execution of voice commands and generates responses."""
    
    _handlers: Dict[str, Callable] = {}
    
    def __init__(self):
        self.last_response: Optional[str] = None
        self.timer_active = False
        self.system = SystemControl()
        
    @classmethod
    def register(cls, intent_name: str):
        """Decorator to register a method as a command handler."""
        def decorator(func: Callable):
            cls._handlers[intent_name] = func
            return func
        return decorator
    
    def handle(self, intent: str, params: Dict[str, Any]) -> str:
        """
        Handle a parsed intent and return the response.
        """
        handler = self._handlers.get(intent, self._handlers.get("unknown"))
        
        if not handler:
            logger.error(f"No handler found for intent: {intent}")
            return "त्रुटि हुई है।" # Generic error in Hindi
            
        try:
            # Bind self to the handler logic (since they are methods)
            response = handler(self, params)
            
            # Store last response for repeat command
            if intent != "repeat":
                self.last_response = response
                
            return response
            
        except Exception as e:
            logger.exception(f"Error handling intent '{intent}': {e}")
            return "माफ कीजिये, कुछ गड़बड़ हो गई।"

    # --- Handlers ---

    @register("greeting")
    def handle_greeting(self, params: Dict[str, Any]) -> str:
        return settings.commands.get("greeting", {}).get("response", "नमस्ते")
    
    @register("get_time")
    def handle_get_time(self, params: Dict[str, Any]) -> str:
        now = datetime.datetime.now()
        hour = now.hour
        # Convert to 12-hour
        period = "सुबह" if hour < 12 else "शाम"
        if hour == 0: hour = 12
        elif hour > 12: hour -= 12
        
        time_str = f"{period} {hour} बजकर {now.minute} मिनट"
        template = settings.commands["get_time"]["response"]
        return template.format(time=time_str)
    
    @register("get_date")
    def handle_get_date(self, params: Dict[str, Any]) -> str:
        now = datetime.datetime.now()
        # Simple Hindi month mapping
        months = ["", "जनवरी", "फरवरी", "मार्च", "अप्रैल", "मई", "जून", 
                  "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]
        date_str = f"{now.day} {months[now.month]} {now.year}"
        return settings.commands["get_date"]["response"].format(date=date_str)

    @register("get_day")
    def handle_get_day(self, params: Dict[str, Any]) -> str:
        now = datetime.datetime.now()
        # Hindi days mapping (0=Monday)
        days = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]
        day_str = days[now.weekday()]
        return settings.commands["get_day"]["response"].format(day=day_str)

    @register("get_weather")
    def handle_get_weather(self, params: Dict[str, Any]) -> str:
        # Placeholder for offline weather
        return settings.commands["get_weather"]["response"]

    @register("thanks")
    def handle_thanks(self, params: Dict[str, Any]) -> str:
        return settings.commands["thanks"]["response"]

    @register("goodbye")
    def handle_goodbye(self, params: Dict[str, Any]) -> str:
        return settings.commands["goodbye"]["response"]

    @register("help")
    def handle_help(self, params: Dict[str, Any]) -> str:
        return settings.commands["help"]["response"]

    @register("set_timer")
    def handle_set_timer(self, params: Dict[str, Any]) -> str:
        duration = params.get("duration", 60)
        self.timer_active = True
        return settings.commands["set_timer"]["response"]

    @register("stop")
    def handle_stop(self, params: Dict[str, Any]) -> str:
        self.timer_active = False
        return settings.commands["stop"]["response"]

    @register("repeat")
    def handle_repeat(self, params: Dict[str, Any]) -> str:
        if self.last_response:
            return self.last_response
        return "कोई पिछला जवाब नहीं है।"

    @register("battery")
    def handle_battery(self, params: Dict[str, Any]) -> str:
        level = self.system.get_battery_level()
        return settings.commands["battery"]["response"].format(battery=level)

    @register("volume_up")
    def handle_volume_up(self, params: Dict[str, Any]) -> str:
        if self.system.adjust_volume(10):
            return settings.commands["volume_up"]["response"]
        return "वॉल्यूम नहीं बढ़ा सका।"

    @register("volume_down")
    def handle_volume_down(self, params: Dict[str, Any]) -> str:
        if self.system.adjust_volume(-10):
            return settings.commands["volume_down"]["response"]
        return "वॉल्यूम कम नहीं कर सका।"

    @register("unknown")
    def handle_unknown(self, params: Dict[str, Any]) -> str:
        return settings.commands.get("unknown", {}).get("response", "क्षमा करें?")

if __name__ == "__main__":
    # Test
    h = CommandHandlers()
    print(h.handle("greeting", {}))
