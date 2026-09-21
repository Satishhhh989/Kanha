from Quartz.CoreGraphics import (
    CGEventCreateMouseEvent,
    CGEventPost,
    kCGHIDEventTap,
    kCGEventMouseMoved,
    kCGEventLeftMouseDown,
    kCGEventLeftMouseUp,
    kCGEventRightMouseDown,
    kCGEventRightMouseUp,
    kCGEventLeftMouseDragged,
    kCGMouseButtonLeft,
    kCGMouseButtonRight,
    CGEventCreateScrollWheelEvent,
    CGEventGetLocation
)
from AppKit import NSEvent
import time
import asyncio

from core.computer.interfaces import MouseController
from core.computer.models import Point
from infrastructure.logging import get_logger

logger = get_logger("sysplatform.macos.mouse")

class MacOSMouseController(MouseController):
    async def move(self, point: Point) -> None:
        event = CGEventCreateMouseEvent(None, kCGEventMouseMoved, (point.x, point.y), 0)
        CGEventPost(kCGHIDEventTap, event)
        logger.debug("Mouse moved", x=point.x, y=point.y)
        await asyncio.sleep(0.01)

    async def click(self, button: str = "left") -> None:
        pos = await self.get_position()
        if button == "right":
            down_event = kCGEventRightMouseDown
            up_event = kCGEventRightMouseUp
            mouse_btn = kCGMouseButtonRight
        else:
            down_event = kCGEventLeftMouseDown
            up_event = kCGEventLeftMouseUp
            mouse_btn = kCGMouseButtonLeft
            
        event_down = CGEventCreateMouseEvent(None, down_event, (pos.x, pos.y), mouse_btn)
        event_up = CGEventCreateMouseEvent(None, up_event, (pos.x, pos.y), mouse_btn)
        
        CGEventPost(kCGHIDEventTap, event_down)
        await asyncio.sleep(0.05)
        CGEventPost(kCGHIDEventTap, event_up)
        logger.debug("Mouse clicked", button=button)

    async def double_click(self, button: str = "left") -> None:
        # For simplicity, send two clicks in rapid succession. True double clicks in Quartz require setting the click state.
        pos = await self.get_position()
        down_event = kCGEventLeftMouseDown
        up_event = kCGEventLeftMouseUp
        mouse_btn = kCGMouseButtonLeft
        
        # Click 1
        event_down = CGEventCreateMouseEvent(None, down_event, (pos.x, pos.y), mouse_btn)
        event_up = CGEventCreateMouseEvent(None, up_event, (pos.x, pos.y), mouse_btn)
        # Quartz expects SetIntegerValueField for click count, but this is a simplified version
        event_down_2 = CGEventCreateMouseEvent(None, down_event, (pos.x, pos.y), mouse_btn)
        event_up_2 = CGEventCreateMouseEvent(None, up_event, (pos.x, pos.y), mouse_btn)
        
        CGEventPost(kCGHIDEventTap, event_down)
        CGEventPost(kCGHIDEventTap, event_up)
        await asyncio.sleep(0.02)
        CGEventPost(kCGHIDEventTap, event_down_2)
        CGEventPost(kCGHIDEventTap, event_up_2)
        logger.debug("Mouse double clicked")

    async def right_click(self) -> None:
        await self.click("right")

    async def scroll(self, clicks: int) -> None:
        # Negative clicks usually mean scroll down
        event = CGEventCreateScrollWheelEvent(None, 0, 1, clicks)
        CGEventPost(kCGHIDEventTap, event)
        logger.debug("Mouse scrolled", clicks=clicks)

    async def drag(self, start: Point, end: Point) -> None:
        await self.move(start)
        event_down = CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, (start.x, start.y), kCGMouseButtonLeft)
        CGEventPost(kCGHIDEventTap, event_down)
        await asyncio.sleep(0.05)
        
        event_drag = CGEventCreateMouseEvent(None, kCGEventLeftMouseDragged, (end.x, end.y), kCGMouseButtonLeft)
        CGEventPost(kCGHIDEventTap, event_drag)
        await asyncio.sleep(0.05)
        
        event_up = CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, (end.x, end.y), kCGMouseButtonLeft)
        CGEventPost(kCGHIDEventTap, event_up)
        logger.debug("Mouse dragged", start=(start.x, start.y), end=(end.x, end.y))

    async def get_position(self) -> Point:
        loc = NSEvent.mouseLocation()
        # Quartz/CoreGraphics uses top-left origin, NSEvent uses bottom-left origin.
        # We need screen height to flip Y.
        from AppKit import NSScreen
        screen_height = NSScreen.mainScreen().frame().size.height
        return Point(x=int(loc.x), y=int(screen_height - loc.y))
