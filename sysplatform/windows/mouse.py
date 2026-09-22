import sys
import asyncio
from core.computer.interfaces import MouseController
from core.computer.models import Point
from infrastructure.logging import get_logger

logger = get_logger("sysplatform.windows.mouse")

# Windows mouse_event constants
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
WHEEL_DELTA = 120

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
else:
    ctypes = None
    POINT = None


class WindowsMouseController(MouseController):
    """Windows mouse controller using Win32 API via ctypes."""

    async def move(self, point: Point) -> None:
        if sys.platform == "win32" and ctypes:
            ctypes.windll.user32.SetCursorPos(int(point.x), int(point.y))
        logger.debug("Mouse moved", x=point.x, y=point.y)
        await asyncio.sleep(0.01)

    async def click(self, button: str = "left") -> None:
        if sys.platform == "win32" and ctypes:
            if button == "right":
                down = MOUSEEVENTF_RIGHTDOWN
                up = MOUSEEVENTF_RIGHTUP
            elif button == "middle":
                down = MOUSEEVENTF_MIDDLEDOWN
                up = MOUSEEVENTF_MIDDLEUP
            else:
                down = MOUSEEVENTF_LEFTDOWN
                up = MOUSEEVENTF_LEFTUP

            ctypes.windll.user32.mouse_event(down, 0, 0, 0, 0)
            await asyncio.sleep(0.05)
            ctypes.windll.user32.mouse_event(up, 0, 0, 0, 0)
        logger.debug("Mouse clicked", button=button)

    async def double_click(self, button: str = "left") -> None:
        await self.click(button)
        await asyncio.sleep(0.05)
        await self.click(button)
        logger.debug("Mouse double clicked", button=button)

    async def right_click(self) -> None:
        await self.click("right")

    async def scroll(self, clicks: int) -> None:
        if sys.platform == "win32" and ctypes:
            delta = clicks * WHEEL_DELTA
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, delta, 0)
        logger.debug("Mouse scrolled", clicks=clicks)

    async def drag(self, start: Point, end: Point) -> None:
        await self.move(start)
        if sys.platform == "win32" and ctypes:
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            await asyncio.sleep(0.05)
            await self.move(end)
            await asyncio.sleep(0.05)
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        logger.debug("Mouse dragged", start=(start.x, start.y), end=(end.x, end.y))

    async def get_position(self) -> Point:
        if sys.platform == "win32" and ctypes and POINT:
            pt = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            return Point(x=int(pt.x), y=int(pt.y))
        return Point(x=0, y=0)
