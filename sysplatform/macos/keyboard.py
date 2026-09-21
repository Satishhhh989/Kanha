from Quartz.CoreGraphics import (
    CGEventCreateKeyboardEvent,
    CGEventPost,
    kCGHIDEventTap
)
import asyncio
from typing import List

from core.computer.interfaces import KeyboardController
from infrastructure.logging import get_logger

logger = get_logger("sysplatform.macos.keyboard")

# A minimal mapping for common keys in Phase 2
MAC_KEY_MAP = {
    "enter": 36,
    "esc": 53,
    "tab": 48,
    "space": 49,
    "delete": 51,
    "up": 126,
    "down": 125,
    "left": 123,
    "right": 124,
    "cmd": 55,
    "shift": 56,
    "ctrl": 59,
    "alt": 58,
}

# Simplified char to keycode for basic typing. 
# A full implementation would use a complete keymap or AppleScript for arbitrary text typing.
# For robustness in Phase 2, we will use AppleScript for type_text as it handles unicode/shifted chars easily.
import subprocess

class MacOSKeyboardController(KeyboardController):
    async def type_text(self, text: str) -> None:
        script = f'''
        tell application "System Events"
            keystroke "{text}"
        end tell
        '''
        try:
            subprocess.run(["osascript", "-e", script], check=True)
            logger.debug("Typed text", text=text)
        except Exception as e:
            logger.error("Failed to type text", error=str(e))
            raise

    async def press_key(self, key: str) -> None:
        keycode = MAC_KEY_MAP.get(key.lower())
        if keycode is None:
            # Fallback to AppleScript for single chars if not in map
            if len(key) == 1:
                await self.type_text(key)
                return
            raise ValueError(f"Unknown key: {key}")
            
        await self.key_down(key)
        await asyncio.sleep(0.01)
        await self.key_up(key)
        logger.debug("Pressed key", key=key)

    async def key_down(self, key: str) -> None:
        keycode = MAC_KEY_MAP.get(key.lower())
        if keycode is not None:
            event = CGEventCreateKeyboardEvent(None, keycode, True)
            CGEventPost(kCGHIDEventTap, event)

    async def key_up(self, key: str) -> None:
        keycode = MAC_KEY_MAP.get(key.lower())
        if keycode is not None:
            event = CGEventCreateKeyboardEvent(None, keycode, False)
            CGEventPost(kCGHIDEventTap, event)

    async def hotkey(self, keys: List[str]) -> None:
        # Simplistic hotkey: down all, up all
        for key in keys:
            await self.key_down(key)
            await asyncio.sleep(0.01)
            
        for key in reversed(keys):
            await self.key_up(key)
            await asyncio.sleep(0.01)
            
        logger.debug("Executed hotkey", keys=keys)
