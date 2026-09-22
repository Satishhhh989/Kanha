import time
from typing import List, Dict
try:
    import mss
    import mss.tools
except ImportError:
    mss = None

from core.computer.interfaces import ScreenCaptureService
from core.computer.models import ScreenFrame
from infrastructure.logging import get_logger

logger = get_logger("sysplatform.windows.screen")

class WindowsScreenCaptureService(ScreenCaptureService):
    """Windows screen capture service using mss."""

    def __init__(self):
        if mss is not None:
            self._sct = mss.mss()
        else:
            self._sct = None
            logger.warning("mss package not installed. Run 'pip install mss' for screen capture support.")

    async def capture_primary_screen(self) -> ScreenFrame:
        if self._sct is None:
            return ScreenFrame(image_data=b"", width=1920, height=1080, display_id="1", timestamp=time.time())
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
        if self._sct is None:
            return [await self.capture_primary_screen()]
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
        if self._sct is None:
            return ScreenFrame(image_data=b"", width=width, height=height, display_id="region", timestamp=time.time())
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
        if self._sct is None:
            return {"width": 1920, "height": 1080}
        monitor = self._sct.monitors[1]
        return {"width": monitor["width"], "height": monitor["height"]}

    async def list_displays(self) -> List[str]:
        if self._sct is None:
            return ["1"]
        return [str(i) for i in range(1, len(self._sct.monitors))]
