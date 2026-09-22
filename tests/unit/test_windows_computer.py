import pytest
from unittest.mock import patch, MagicMock

from core.computer.interfaces import ComputerController
from sysplatform.windows.computer import WindowsComputerController

def test_windows_computer_controller_initialization():
    controller = WindowsComputerController()
    assert isinstance(controller, ComputerController)
    assert controller.application is not None
    assert controller.window is not None
    assert controller.mouse is not None
    assert controller.keyboard is not None
    assert controller.clipboard is not None
    assert controller.screen is not None
    assert controller.observer is not None

@pytest.mark.asyncio
async def test_windows_application_controller_is_running():
    from sysplatform.windows.application import WindowsApplicationController
    app_ctrl = WindowsApplicationController()
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout='"notepad.exe","1234","Console","1","10,000 K"\n')
        is_running = await app_ctrl.is_application_running("notepad")
        assert is_running is True

        is_running_false = await app_ctrl.is_application_running("calc")
        assert is_running_false is False

@pytest.mark.asyncio
async def test_windows_observer_state():
    from sysplatform.windows.observer import WindowsComputerObserver
    
    mock_app = MagicMock()
    mock_app.get_active_application = MagicMock(return_value="chrome")
    
    mock_win = MagicMock()
    mock_win.get_active_window = MagicMock(return_value={"name": "Google", "id": "100"})
    
    mock_mouse = MagicMock()
    from core.computer.models import Point
    mock_mouse.get_position = MagicMock(return_value=Point(x=50, y=50))
    
    mock_screen = MagicMock()
    mock_screen.get_screen_dimensions = MagicMock(return_value={"width": 1920, "height": 1080})
    mock_screen.list_displays = MagicMock(return_value=["1"])
    
    async def async_app(): return "chrome"
    async def async_win(): return {"name": "Google", "id": "100"}
    async def async_mouse(): return Point(x=50, y=50)
    async def async_dims(): return {"width": 1920, "height": 1080}
    async def async_displays(): return ["1"]
    
    mock_app.get_active_application = async_app
    mock_win.get_active_window = async_win
    mock_mouse.get_position = async_mouse
    mock_screen.get_screen_dimensions = async_dims
    mock_screen.list_displays = async_displays
    
    observer = WindowsComputerObserver(mock_app, mock_win, mock_mouse, mock_screen)
    state = await observer.get_state()
    
    assert state.active_application == "chrome"
    assert state.active_window == "Google"
    assert state.mouse_position.x == 50
    assert state.screen_dimensions["width"] == 1920
