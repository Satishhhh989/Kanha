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

from .application import MacOSApplicationController
from .window import MacOSWindowController
from .mouse import MacOSMouseController
from .keyboard import MacOSKeyboardController
from .clipboard import MacOSClipboardController
from .screen import MacOSScreenCaptureService
from .observer import MacOSComputerObserver

class MacOSComputerController(ComputerController):
    def __init__(self):
        self._application = MacOSApplicationController()
        self._window = MacOSWindowController()
        self._mouse = MacOSMouseController()
        self._keyboard = MacOSKeyboardController()
        self._clipboard = MacOSClipboardController()
        self._screen = MacOSScreenCaptureService()
        
        from infrastructure.browser.playwright_controller import PlaywrightBrowserController
        self._browser = PlaywrightBrowserController()
        
        self._observer = MacOSComputerObserver(
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
