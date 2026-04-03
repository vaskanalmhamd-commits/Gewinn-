import os
import subprocess
import logging
import asyncio
from database import db_manager

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ConditionGuard')

class ConditionGuard:
    """The Gatekeeper ensuring DePIN workers only run on AC + Wi-Fi."""

    _instance = None
    _status = {"ac_power": False, "wifi": False, "active": False}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConditionGuard, cls).__new__(cls)
        return cls._instance

    def check_conditions(self):
        """Monitor Power and Network status (Termux/Linux context)."""
        # 1. Check Power (AC vs Battery)
        ac_power = self._check_power_ac()

        # 2. Check Network (Wi-Fi vs Mobile)
        wifi_connected = self._check_wifi_status()

        self._status["ac_power"] = ac_power
        self._status["wifi"] = wifi_connected
        self._status["active"] = ac_power and wifi_connected

        return self._status

    def _check_power_ac(self) -> bool:
        """Check if AC power is connected using termux-api or sysfs."""
        try:
            # Method A: termux-battery-status (requires termux-api)
            # res = subprocess.check_output(["termux-battery-status"], timeout=2)
            # data = json.loads(res)
            # return data.get('plugged') != 'UNPLUGGED'

            # Method B: sysfs fallback (common on Android/Linux)
            if os.path.exists("/sys/class/power_supply/AC/online"):
                with open("/sys/class/power_supply/AC/online", 'r') as f:
                    return f.read().strip() == "1"
            elif os.path.exists("/sys/class/power_supply/usb/online"):
                 with open("/sys/class/power_supply/usb/online", 'r') as f:
                    return f.read().strip() == "1"

            # Default to True for non-mobile environments (testing)
            return True
        except:
            return True

    def _check_wifi_status(self) -> bool:
        """Check if Wi-Fi is the active network interface."""
        try:
            # Method A: ip route (Linux/Android)
            res = subprocess.check_output(["ip", "route", "get", "8.8.8.8"], stderr=subprocess.STDOUT, timeout=2).decode()
            # If the route goes through 'wlan0', it's Wi-Fi
            return "wlan" in res or "wifi" in res
        except:
            # Default to True if we cannot determine (testing)
            return True

    async def guard_loop(self):
        """Background monitor to auto-pause/resume DePIN workers."""
        from depin_manager import depin_manager
        logger.info("Condition Guard monitoring started.")

        while True:
            try:
                status = self.check_conditions()
                if not status["active"]:
                    # Pause all DePIN workers to save battery/data
                    if depin_manager.active_tasks:
                        logger.warning("Conditions NOT met (No AC or Wi-Fi). Pausing DePIN workers...")
                        for name, task in depin_manager.active_tasks.items():
                             if not task.done(): task.cancel()
                        depin_manager.active_tasks = {}
                        # Update status in DB
                        for net in depin_manager.workers.keys():
                             db_manager.update_depin_status(net, status="Paused (Conditions)")
                else:
                    # Conditions met: Ensure workers are running
                    if not depin_manager.active_tasks:
                        logger.info("Conditions met (AC + Wi-Fi). Resuming DePIN workers...")
                        depin_manager.start_all()
            except Exception as e:
                logger.error(f"Error in Condition Guard loop: {e}")

            await asyncio.sleep(60) # Check every minute

# Global instance
condition_guard = ConditionGuard()
