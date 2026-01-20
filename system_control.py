"""
System Control Abstraction for Raspberry Pi / Linux.
Handles hardware interactions: Volume, Battery, Power.
"""
import subprocess
import os
import glob
from typing import Optional
from logger import get_logger

logger = get_logger("system_control")

class SystemControl:
    """
    Abstracts system-level operations.
    Supports RPiOS specific introspection for Mixer and Battery.
    """
    
    def __init__(self):
        self._mixer_control = self._detect_alsa_mixer()
    
    def _detect_alsa_mixer(self) -> str:
        """Autodetect available ALSA mixer control."""
        try:
            # List controls
            result = subprocess.run(
                ["amixer", "scontrols"], 
                capture_output=True, 
                text=True
            )
            output = result.stdout
            
            # Priority list for controls
            candidates = ["Master", "PCM", "Speaker", "HDMI"]
            for candidate in candidates:
                if f"'{candidate}'" in output:
                    logger.info(f"Using ALSA Mixer Control: {candidate}")
                    return candidate
            
            logger.warning("No standard mixer control found. Volume control may fail.")
            return "Master"  # Default fallback
            
        except FileNotFoundError:
            logger.error("amixer command not found. Is alsa-utils installed?")
            return "Master"
    
    def get_battery_level(self) -> int:
        """
        Get battery level percentage.
        Supports standard sysfs and common UPS HATs via I2C check behavior.
        """
        # 1. Standard Linux System Class (Laptops / some implementations)
        try:
            battery_path = "/sys/class/power_supply/BAT0/capacity"
            if os.path.exists(battery_path):
                with open(battery_path, 'r') as f:
                    return int(f.read().strip())
        except Exception:
            pass

        # 2. Raspberry Pi UPS HATs mostly simulate this or are on I2C.
        # Check all power supplies
        try:
            paths = glob.glob("/sys/class/power_supply/*/capacity")
            if paths:
                with open(paths[0], 'r') as f:
                    return int(f.read().strip())
        except Exception:
            pass
            
        # 3. Fallback: Assume AC Power (100%)
        logger.debug("No battery detected, assuming AC power.")
        return 100

    def adjust_volume(self, delta_percent: int) -> bool:
        """
        Adjust volume by delta percentage.
        Returns True if successful.
        """
        if not self._mixer_control:
            return False
            
        sign = "+" if delta_percent > 0 else "-"
        amount = f"{abs(delta_percent)}%"
        cmd = ["amixer", "set", self._mixer_control, f"{amount}{sign}"]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            logger.info(f"Volume adjusted: {sign}{amount}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to adjust volume: {e}")
            return False
        except FileNotFoundError:
            return False

    def reboot(self):
        """Reboot the system."""
        try:
            subprocess.run(["sudo", "reboot"], check=True)
        except Exception as e:
            logger.error(f"Reboot failed: {e}")

    def shutdown(self):
        """Shutdown the system."""
        try:
            subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
        except Exception as e:
            logger.error(f"Shutdown failed: {e}")
