import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from core.computer.models import ComputerAction, ActionType, Point
from core.computer.executor import ActionExecutor
from core.errors import ToolExecutionError

@pytest.fixture
def mock_controller():
    controller = MagicMock()
    controller.application = AsyncMock()
    controller.window = AsyncMock()
    controller.mouse = AsyncMock()
    controller.keyboard = AsyncMock()
    controller.clipboard = AsyncMock()
    controller.screen = AsyncMock()
    controller.browser = AsyncMock()
    
    # Mock some basic success scenarios for verification
    controller.application.is_application_running.return_value = True
    controller.window.get_active_window.return_value = {"id": "123", "name": "Test"}
    controller.clipboard.read_clipboard.return_value = "test_text"
    controller.browser.get_current_url.return_value = "https://example.com"
    return controller

@pytest.mark.asyncio
async def test_action_executor_success(mock_controller):
    executor = ActionExecutor(mock_controller)
    action = ComputerAction(action_type=ActionType.OPEN_APPLICATION, target="Safari")
    
    result = await executor.execute(action)
    
    assert result["status"] == "success"
    mock_controller.application.open_application.assert_called_once_with("Safari")
    mock_controller.application.is_application_running.assert_called_once_with("Safari")

@pytest.mark.asyncio
async def test_action_executor_verification_failure(mock_controller):
    # Make verification fail
    mock_controller.application.is_application_running.return_value = False
    
    executor = ActionExecutor(mock_controller)
    action = ComputerAction(action_type=ActionType.OPEN_APPLICATION, target="Safari")
    
    with pytest.raises(ToolExecutionError, match="failed verification"):
        await executor.execute(action)

@pytest.mark.asyncio
async def test_action_executor_timeout(mock_controller):
    async def slow_open(name):
        await asyncio.sleep(0.5)
        
    mock_controller.application.open_application.side_effect = slow_open
    
    executor = ActionExecutor(mock_controller)
    # Set timeout extremely low
    action = ComputerAction(action_type=ActionType.OPEN_APPLICATION, target="Safari", timeout=0.1)
    
    with pytest.raises(ToolExecutionError, match="timed out"):
        await executor.execute(action)

@pytest.mark.asyncio
async def test_mouse_move_validation(mock_controller):
    executor = ActionExecutor(mock_controller)
    
    # Missing x and y
    action = ComputerAction(action_type=ActionType.MOUSE_MOVE, parameters={})
    with pytest.raises(ToolExecutionError, match="failed"):
        await executor.execute(action)
        
    # Valid parameters
    action_valid = ComputerAction(action_type=ActionType.MOUSE_MOVE, parameters={"x": 100, "y": 200})
    await executor.execute(action_valid)
    
    # We must extract the argument to assert correctly because Point is constructed inside
    called_args = mock_controller.mouse.move.call_args[0]
    assert called_args[0].x == 100
    assert called_args[0].y == 200
