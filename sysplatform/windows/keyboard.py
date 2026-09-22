import sys
import asyncio
from typing import List
from core.computer.interfaces import KeyboardController
from infrastructure.logging import get_logger

logger = get_logger("sysplatform.windows.keyboard")

# Windows Virtual-Key Codes
WIN_KEY_MAP = {
    "enter": 0x0D,
    "return": 0x0D,
    "esc": 0x1B,
    "escape": 0x1B,
    "tab": 0x09,
    "space": 0x20,
    "backspace": 0x08,
    "delete": 0x2E,
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
    "shift": 0x10,
    "ctrl": 0x11,
    "control": 0x11,
    "alt": 0x12,
    "win": 0x5B,
    "cmd": 0x5B,
}

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
INPUT_KEYBOARD = 1

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_ulonglong)
        ]

    class INPUT(ctypes.Structure):
        class _INPUT(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT)]
        _anonymous_ = ("_input",)
        _fields_ = [
            ("type", wintypes.DWORD),
            ("_input", _INPUT)
        ]
else:
    ctypes = None
    KEYBDINPUT = None
    INPUT = None


class WindowsKeyboardController(KeyboardController):
    """Windows keyboard controller using Win32 API via ctypes."""

    async def type_text(self, text: str) -> None:
        if sys.platform == "win32" and ctypes and INPUT:
            for char in text:
                # Key down
                inp_down = INPUT(type=INPUT_KEYBOARD)
                inp_down.ki = KEYBDINPUT(
                    wVk=0,
                    wScan=ord(char),
                    dwFlags=KEYEVENTF_UNICODE,
                    time=0,
                    dwExtraInfo=0
                )
                ctypes.windll.user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(INPUT))

                # Key up
                inp_up = INPUT(type=INPUT_KEYBOARD)
                inp_up.ki = KEYBDINPUT(
                    wVk=0,
                    wScan=ord(char),
                    dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP,
                    time=0,
                    dwExtraInfo=0
                )
                ctypes.windll.user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(INPUT))
                await asyncio.sleep(0.005)

        logger.debug("Typed text", text=text)

    async def press_key(self, key: str) -> None:
        await self.key_down(key)
        await asyncio.sleep(0.02)
        await self.key_up(key)
        logger.debug("Pressed key", key=key)

    async def key_down(self, key: str) -> None:
        vk = WIN_KEY_MAP.get(key.lower())
        if vk is None and len(key) == 1:
            await self.type_text(key)
            return

        if vk is not None and sys.platform == "win32" and ctypes:
            ctypes.windll.user32.keybd_event(vk, 0, 0, 0)

    async def key_up(self, key: str) -> None:
        vk = WIN_KEY_MAP.get(key.lower())
        if vk is not None and sys.platform == "win32" and ctypes:
            ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

    async def hotkey(self, keys: List[str]) -> None:
        for key in keys:
            await self.key_down(key)
            await asyncio.sleep(0.01)

        for key in reversed(keys):
            await self.key_up(key)
            await asyncio.sleep(0.01)

        logger.debug("Executed hotkey", keys=keys)
