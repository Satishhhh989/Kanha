import subprocess
from typing import List, Dict, Optional
from core.computer.interfaces import WindowController
from infrastructure.logging import get_logger

logger = get_logger("sysplatform.macos.window")

class MacOSWindowController(WindowController):
    async def list_windows(self) -> List[Dict]:
        # Basic implementation using AppleScript to get windows of frontmost app
        script = """
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            set windowList to {}
            repeat with w in windows of frontApp
                set end of windowList to {name of w, id of w}
            end repeat
            return windowList
        end tell
        """
        try:
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=True)
            # Output is comma separated list of name, id, name, id
            raw = result.stdout.strip()
            if not raw:
                return []
            parts = [p.strip() for p in raw.split(",")]
            windows = []
            for i in range(0, len(parts), 2):
                if i + 1 < len(parts):
                    windows.append({"name": parts[i], "id": parts[i+1]})
            return windows
        except Exception as e:
            logger.error("Failed to list windows", error=str(e))
            return []

    async def get_active_window(self) -> Optional[Dict]:
        windows = await self.list_windows()
        if windows:
            return windows[0]
        return None

    async def focus_window(self, window_id: str) -> None:
        # Note: Depending on the app, window_id might be hard to focus explicitly without app name.
        # A simpler version for Phase 2: just bring the app to front.
        # We will attempt to use AppleScript to focus if we have enough info, otherwise we log a limitation.
        logger.warning("Focus window by ID is a stub in Phase 2 on macOS using AppleScript.")
        pass

    async def minimize_window(self, window_id: str) -> None:
        pass

    async def maximize_window(self, window_id: str) -> None:
        pass

    async def restore_window(self, window_id: str) -> None:
        pass

    async def move_window(self, window_id: str, x: int, y: int) -> None:
        pass

    async def resize_window(self, window_id: str, width: int, height: int) -> None:
        pass
