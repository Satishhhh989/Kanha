import asyncio
from typing import Any, Dict, Optional
from core.computer.models import ComputerAction, ActionType
from core.computer.interfaces import ComputerController
from core.computer.verification import verification_engine
from infrastructure.logging import get_logger
from core.errors import ToolExecutionError

logger = get_logger("core.computer.executor")

class ActionExecutor:
    """Executes a ComputerAction against a ComputerController with timeout and verification."""
    
    def __init__(self, controller: ComputerController):
        self.controller = controller

    async def execute(self, action: ComputerAction) -> Dict[str, Any]:
        """
        Executes the action, enforces timeout, and verifies the outcome.
        Raises ToolExecutionError on failure or timeout.
        """
        logger.info("Executing action", action_id=action.action_id, action_type=action.action_type)
        
        try:
            # Enforce timeout using asyncio.wait_for
            result = await asyncio.wait_for(
                self._dispatch(action),
                timeout=action.timeout
            )
            
            # Verify action success
            is_verified = await verification_engine.verify_action(action, self.controller)
            
            if not is_verified:
                raise ToolExecutionError(f"Action {action.action_type} failed verification.")
                
            return {
                "status": "success",
                "action_id": action.action_id,
                "result": result
            }
            
        except asyncio.TimeoutError:
            logger.error("Action timed out", action_id=action.action_id, timeout=action.timeout)
            raise ToolExecutionError(f"Action {action.action_type} timed out after {action.timeout} seconds.")
        except Exception as e:
            logger.error("Action execution failed", action_id=action.action_id, error=str(e))
            raise ToolExecutionError(f"Action {action.action_type} failed: {str(e)}")

    async def _dispatch(self, action: ComputerAction) -> Any:
        """Dispatches the action to the appropriate controller method."""
        
        if action.action_type == ActionType.OPEN_APPLICATION:
            if not action.target:
                raise ValueError("Target application name is required.")
            return await self.controller.application.open_application(action.target)
            
        elif action.action_type == ActionType.CLOSE_APPLICATION:
            if not action.target:
                raise ValueError("Target application name is required.")
            return await self.controller.application.close_application(action.target)
            
        elif action.action_type == ActionType.FOCUS_WINDOW:
            if not action.target:
                raise ValueError("Target window ID is required.")
            return await self.controller.window.focus_window(action.target)
            
        elif action.action_type == ActionType.MOUSE_MOVE:
            x = action.parameters.get("x")
            y = action.parameters.get("y")
            if x is None or y is None:
                raise ValueError("x and y parameters are required for MOUSE_MOVE.")
            from core.computer.models import Point
            return await self.controller.mouse.move(Point(x=x, y=y))
            
        elif action.action_type == ActionType.MOUSE_CLICK:
            button = action.parameters.get("button", "left")
            return await self.controller.mouse.click(button)
            
        elif action.action_type == ActionType.KEY_TYPE:
            text = action.parameters.get("text")
            if not text:
                raise ValueError("text parameter is required for KEY_TYPE.")
            return await self.controller.keyboard.type_text(text)
            
        elif action.action_type == ActionType.KEY_HOTKEY:
            keys = action.parameters.get("keys")
            if not keys or not isinstance(keys, list):
                raise ValueError("keys parameter (list) is required for KEY_HOTKEY.")
            return await self.controller.keyboard.hotkey(keys)
            
        elif action.action_type == ActionType.CLIPBOARD_WRITE:
            text = action.parameters.get("text")
            if text is None:
                raise ValueError("text parameter is required for CLIPBOARD_WRITE.")
            return await self.controller.clipboard.write_clipboard(text)
            
        elif action.action_type == ActionType.SCREEN_CAPTURE:
            return await self.controller.screen.capture_primary_screen()
            
        elif action.action_type == ActionType.BROWSER_NAVIGATE:
            url = action.parameters.get("url")
            if not url:
                raise ValueError("url parameter is required for BROWSER_NAVIGATE.")
            return await self.controller.browser.navigate(url)
            
        # Add other dispatches as needed
        raise NotImplementedError(f"Action type {action.action_type} is not yet implemented in ActionExecutor.")
