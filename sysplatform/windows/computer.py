from core.computer.interfaces import (
    ComputerController,
    ApplicationController,
    WindowController,
    MouseController,
    KeyboardController,
    ClipboardController,
    ScreenCaptureService,
    ComputerObserver
)
from infrastructure.logging import get_logger

from .application import WindowsApplicationController
from .window import WindowsWindowController
from .mouse import WindowsMouseController
from .keyboard import WindowsKeyboardController
from .clipboard import WindowsClipboardController
from .screen import WindowsScreenCaptureService
from .observer import WindowsComputerObserver

logger = get_logger("sysplatform.windows.computer")

class WindowsComputerController(ComputerController):
    """Full Windows implementation of the ComputerController interface."""

    def __init__(self):
        self._application = WindowsApplicationController()
        self._window = WindowsWindowController()
        self._mouse = WindowsMouseController()
        self._keyboard = WindowsKeyboardController()
        self._clipboard = WindowsClipboardController()
        self._screen = WindowsScreenCaptureService()

        try:
            from infrastructure.browser.playwright_controller import PlaywrightBrowserController
            self._browser = PlaywrightBrowserController()
        except Exception as e:
            logger.warning("Playwright browser controller unavailable", error=str(e))
            self._browser = None

        self._observer = WindowsComputerObserver(
            app_ctrl=self._application,
            win_ctrl=self._window,
            mouse_ctrl=self._mouse,
            screen_ctrl=self._screen
        )

    @property
    def application(self) -> ApplicationController:
        return self._application

    @property
    def window(self) -> WindowController:
        return self._window

    @property
    def mouse(self) -> MouseController:
        return self._mouse

    @property
    def keyboard(self) -> KeyboardController:
        return self._keyboard

    @property
    def clipboard(self) -> ClipboardController:
        return self._clipboard

    @property
    def screen(self) -> ScreenCaptureService:
        return self._screen

    @property
    def browser(self):
        return self._browser

    @property
    def observer(self) -> ComputerObserver:
        return self._observer
