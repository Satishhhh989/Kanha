import subprocess
from typing import List, Dict, Optional
from AppKit import NSWorkspace
from core.computer.interfaces import ApplicationController
from infrastructure.logging import get_logger

logger = get_logger("sysplatform.macos.application")

class MacOSApplicationController(ApplicationController):
    async def list_applications(self) -> List[str]:
        # Simple implementation: list /Applications
        try:
            result = subprocess.run(["ls", "/Applications"], capture_output=True, text=True, check=True)
            apps = [line.replace(".app", "") for line in result.stdout.splitlines() if line.endswith(".app")]
            return apps
        except Exception as e:
            logger.error("Failed to list applications", error=str(e))
            return []
            
    async def open_application(self, name: str) -> None:
        try:
            subprocess.run(["open", "-a", name], check=True)
            logger.debug("Opened application", app_name=name)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to open application", app_name=name, error=str(e))
            raise Exception(f"Could not open application: {name}")

    async def close_application(self, name: str) -> None:
        # Using AppleScript or killall
        try:
            subprocess.run(["osascript", "-e", f'quit app "{name}"'], check=True, capture_output=True)
            logger.debug("Closed application", app_name=name)
        except subprocess.CalledProcessError as e:
            logger.warning("Failed to close gracefully, trying killall", app_name=name)
            try:
                subprocess.run(["killall", name], check=True, capture_output=True)
            except Exception as e2:
                logger.error("Failed to kill application", app_name=name, error=str(e2))
                raise Exception(f"Could not close application: {name}")

    async def is_application_running(self, name: str) -> bool:
        workspace = NSWorkspace.sharedWorkspace()
        running_apps = workspace.runningApplications()
        name_lower = name.lower()
        for app in running_apps:
            if app.localizedName() and app.localizedName().lower() == name_lower:
                return True
        return False

    async def get_application_info(self, name: str) -> Dict:
        workspace = NSWorkspace.sharedWorkspace()
        running_apps = workspace.runningApplications()
        name_lower = name.lower()
        for app in running_apps:
            if app.localizedName() and app.localizedName().lower() == name_lower:
                return {
                    "name": app.localizedName(),
                    "pid": app.processIdentifier(),
                    "is_active": app.isActive(),
                    "bundle_id": app.bundleIdentifier()
                }
        return {"name": name, "status": "not running"}

    async def get_active_application(self) -> Optional[str]:
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.frontmostApplication()
        if active_app:
            return active_app.localizedName()
        return None
