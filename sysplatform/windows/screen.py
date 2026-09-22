import time
from typing import List, Dict
import mss
import mss.tools

from core.computer.interfaces import ScreenCaptureService
from core.computer.models import ScreenFrame
from infrastructure.logging import get_logger

logger = get_logger("sysplatform.windows.screen")

class WindowsScreenCaptureService(ScreenCaptureService):
    """Windows screen capture service using mss."""

    def __init__(self):
        self._sct = mss.mss()

    async def capture_primary_screen(self) -> ScreenFrame:
        # Monitor 1 is the primary monitor in mss (monitor 0 is all monitors combined)
        monitor = self._sct.monitors[1]
        sct_img = self._sct.grab(monitor)
        
        logger.debug("Captured primary screen", width=sct_img.width, height=sct_img.height)
        png_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)
        return ScreenFrame(
            image_data=png_bytes,
            width=sct_img.width,
            height=sct_img.height,
            display_id="1",
            timestamp=time.time()
        )

    async def capture_all_screens(self) -> List[ScreenFrame]:
        frames = []
        for i, monitor in enumerate(self._sct.monitors[1:], 1):
            sct_img = self._sct.grab(monitor)
            frames.append(ScreenFrame(
                image_data=mss.tools.to_png(sct_img.rgb, sct_img.size),
                width=sct_img.width,
                height=sct_img.height,
                display_id=str(i),
                timestamp=time.time()
            ))
        return frames

    async def capture_region(self, x: int, y: int, width: int, height: int) -> ScreenFrame:
        region = {"top": y, "left": x, "width": width, "height": height}
        sct_img = self._sct.grab(region)
        return ScreenFrame(
            image_data=mss.tools.to_png(sct_img.rgb, sct_img.size),
            width=sct_img.width,
            height=sct_img.height,
            display_id="region",
            timestamp=time.time()
        )

    async def get_screen_dimensions(self) -> Dict[str, int]:
        monitor = self._sct.monitors[1]
        return {"width": monitor["width"], "height": monitor["height"]}

    async def list_displays(self) -> List[str]:
        return [str(i) for i in range(1, len(self._sct.monitors))]
