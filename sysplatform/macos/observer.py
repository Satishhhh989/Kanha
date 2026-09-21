from core.computer.interfaces import ComputerObserver, ApplicationController, WindowController, MouseController, ScreenCaptureService
from core.computer.models import ComputerState

class MacOSComputerObserver(ComputerObserver):
    def __init__(
        self, 
        app_ctrl: ApplicationController, 
        win_ctrl: WindowController, 
        mouse_ctrl: MouseController,
        screen_ctrl: ScreenCaptureService
    ):
        self.app_ctrl = app_ctrl
        self.win_ctrl = win_ctrl
        self.mouse_ctrl = mouse_ctrl
        self.screen_ctrl = screen_ctrl

    async def get_state(self) -> ComputerState:
        active_app = await self.app_ctrl.get_active_application()
        
        active_win_dict = await self.win_ctrl.get_active_window()
        active_win_name = active_win_dict.get("name") if active_win_dict else None
        
        dims = await self.screen_ctrl.get_screen_dimensions()
        pos = await self.mouse_ctrl.get_position()
        
        running_apps = await self.app_ctrl.list_applications() # Or running, but list_applications right now lists /Applications. Let's fix that.
        
        displays = await self.screen_ctrl.list_displays()
        
        return ComputerState(
            active_application=active_app,
            active_window=active_win_name,
            screen_dimensions=dims,
            mouse_position=pos,
            clipboard_state=None, # Excluded for privacy by default
            running_applications=[], # Too slow to get all running apps every time in basic implementation without a dedicated method
            available_displays=displays
        )
