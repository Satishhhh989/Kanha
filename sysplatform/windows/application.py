import sys
import subprocess
from typing import List, Dict, Optional
from core.computer.interfaces import ApplicationController
from infrastructure.logging import get_logger

logger = get_logger("sysplatform.windows.application")

class WindowsApplicationController(ApplicationController):
    """Windows application controller using standard Windows commands and Win32."""

    async def list_applications(self) -> List[str]:
        """Lists running applications by querying visible process tasks."""
        apps = set()
        try:
            res = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                check=True
            )
            for line in res.stdout.splitlines():
                if line.strip():
                    parts = line.split('","')
                    if parts:
                        proc_name = parts[0].strip('"')
                        if proc_name.lower().endswith(".exe"):
                            apps.add(proc_name[:-4])
                        else:
                            apps.add(proc_name)
            return sorted(list(apps))
        except Exception as e:
            logger.error("Failed to list applications", error=str(e))
            return []

    async def open_application(self, name: str) -> None:
        """Opens an application on Windows."""
        logger.info("Opening application", app_name=name)
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "", name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True
            )
            logger.debug("Opened application", app_name=name)
        except Exception as e:
            logger.error("Failed to open application", app_name=name, error=str(e))
            raise Exception(f"Could not open application: {name}")

    async def close_application(self, name: str) -> None:
        """Closes an application on Windows using taskkill."""
        logger.info("Closing application", app_name=name)
        exe_name = name if name.lower().endswith(".exe") else f"{name}.exe"
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", exe_name],
                check=True,
                capture_output=True
            )
            logger.debug("Closed application", app_name=name)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to close application", app_name=name, error=str(e))
            raise Exception(f"Could not close application: {name}")

    async def is_application_running(self, name: str) -> bool:
        """Checks whether a given application or process is running."""
        exe_name = name.lower()
        if not exe_name.endswith(".exe"):
            exe_name += ".exe"

        try:
            res = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True
            )
            return any(exe_name in line.lower() for line in res.stdout.splitlines())
        except Exception as e:
            logger.error("Failed to check if application is running", error=str(e))
            return False

    async def get_application_info(self, name: str) -> Dict:
        """Returns details for an application."""
        is_running = await self.is_application_running(name)
        return {
            "name": name,
            "is_running": is_running,
            "status": "running" if is_running else "not running"
        }

    async def get_active_application(self) -> Optional[str]:
        """Returns the name/title of the currently active foreground window."""
        if sys.platform != "win32":
            return None

        import ctypes
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if hwnd:
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value.strip()
                    return title or None
        except Exception as e:
            logger.error("Failed to get active application", error=str(e))
        return None
