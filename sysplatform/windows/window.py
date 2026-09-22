import sys
from typing import List, Dict, Optional
from core.computer.interfaces import WindowController
from infrastructure.logging import get_logger

logger = get_logger("sysplatform.windows.window")

# ShowWindow commands
SW_MAXIMIZE = 3
SW_MINIMIZE = 6
SW_RESTORE = 9

# SetWindowPos flags
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004

class WindowsWindowController(WindowController):
    """Windows window controller using Win32 API via ctypes."""

    async def list_windows(self) -> List[Dict]:
        windows = []
        if sys.platform != "win32":
            return windows

        import ctypes
        from ctypes import wintypes

        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

        def enum_callback(hwnd, _):
            if ctypes.windll.user32.IsWindowVisible(hwnd):
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value.strip()
                    if title:
                        windows.append({"name": title, "id": str(hwnd)})
            return True

        try:
            ctypes.windll.user32.EnumWindows(EnumWindowsProc(enum_callback), 0)
        except Exception as e:
            logger.error("Failed to list windows", error=str(e))

        return windows

    async def get_active_window(self) -> Optional[Dict]:
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
                    return {"name": buf.value.strip(), "id": str(hwnd)}
                return {"name": "", "id": str(hwnd)}
        except Exception as e:
            logger.error("Failed to get active window", error=str(e))
        return None

    async def focus_window(self, window_id: str) -> None:
        if sys.platform != "win32":
            return

        import ctypes
        try:
            hwnd = int(window_id)
            ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            logger.debug("Focused window", window_id=window_id)
        except Exception as e:
            logger.error("Failed to focus window", window_id=window_id, error=str(e))

    async def minimize_window(self, window_id: str) -> None:
        if sys.platform != "win32":
            return

        import ctypes
        try:
            hwnd = int(window_id)
            ctypes.windll.user32.ShowWindow(hwnd, SW_MINIMIZE)
            logger.debug("Minimized window", window_id=window_id)
        except Exception as e:
            logger.error("Failed to minimize window", window_id=window_id, error=str(e))

    async def maximize_window(self, window_id: str) -> None:
        if sys.platform != "win32":
            return

        import ctypes
        try:
            hwnd = int(window_id)
            ctypes.windll.user32.ShowWindow(hwnd, SW_MAXIMIZE)
            logger.debug("Maximized window", window_id=window_id)
        except Exception as e:
            logger.error("Failed to maximize window", window_id=window_id, error=str(e))

    async def restore_window(self, window_id: str) -> None:
        if sys.platform != "win32":
            return

        import ctypes
        try:
            hwnd = int(window_id)
            ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
            logger.debug("Restored window", window_id=window_id)
        except Exception as e:
            logger.error("Failed to restore window", window_id=window_id, error=str(e))

    async def move_window(self, window_id: str, x: int, y: int) -> None:
        if sys.platform != "win32":
            return

        import ctypes
        try:
            hwnd = int(window_id)
            ctypes.windll.user32.SetWindowPos(hwnd, 0, int(x), int(y), 0, 0, SWP_NOSIZE | SWP_NOZORDER)
            logger.debug("Moved window", window_id=window_id, x=x, y=y)
        except Exception as e:
            logger.error("Failed to move window", window_id=window_id, error=str(e))

    async def resize_window(self, window_id: str, width: int, height: int) -> None:
        if sys.platform != "win32":
            return

        import ctypes
        try:
            hwnd = int(window_id)
            ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, int(width), int(height), SWP_NOMOVE | SWP_NOZORDER)
            logger.debug("Resized window", window_id=window_id, width=width, height=height)
        except Exception as e:
            logger.error("Failed to resize window", window_id=window_id, error=str(e))
