from typing import Any
from pydantic import BaseModel, Field
from core.tools.base import BaseTool
from core.security import RiskLevel
from core.computer.models import ComputerAction, ActionType
from core.computer.executor import ActionExecutor
from core.computer.interfaces import ComputerController

class ClickSchema(BaseModel):
    button: str = Field(default="left", description="The mouse button to click: 'left', 'right', or 'middle'.")

class TypeSchema(BaseModel):
    text: str = Field(..., description="The text to type.")

class ComputerActionTool(BaseTool):
    """Base for tools that execute a ComputerAction."""
    
    def __init__(self, controller: ComputerController):
        self.executor = ActionExecutor(controller)

class ClickTool(ComputerActionTool):
    @property
    def name(self) -> str: return "click"
    
    @property
    def description(self) -> str: return "Clicks the mouse at the current position."
    
    @property
    def input_schema(self) -> type[BaseModel]: return ClickSchema
    
    @property
    def risk_level(self) -> RiskLevel: return RiskLevel.COMPUTER_INTERACTION
    
    async def execute(self, button: str = "left", **kwargs: Any) -> Any:
        action = ComputerAction(action_type=ActionType.MOUSE_CLICK, parameters={"button": button})
        return await self.executor.execute(action)

class TypeTextTool(ComputerActionTool):
    @property
    def name(self) -> str: return "type_text"
    
    @property
    def description(self) -> str: return "Types the specified text on the keyboard."
    
    @property
    def input_schema(self) -> type[BaseModel]: return TypeSchema
    
    @property
    def risk_level(self) -> RiskLevel: return RiskLevel.COMPUTER_INTERACTION
    
    async def execute(self, text: str, **kwargs: Any) -> Any:
        action = ComputerAction(action_type=ActionType.KEY_TYPE, parameters={"text": text})
        return await self.executor.execute(action)

class ScreenCaptureSchema(BaseModel):
    pass

class ScreenCaptureTool(ComputerActionTool):
    @property
    def name(self) -> str: return "capture_screen"
    
    @property
    def description(self) -> str: return "Captures the primary screen and returns the frame metadata."
    
    @property
    def input_schema(self) -> type[BaseModel]: return ScreenCaptureSchema
    
    @property
    def risk_level(self) -> RiskLevel: return RiskLevel.SENSITIVE_DATA
    
    async def execute(self, **kwargs: Any) -> Any:
        action = ComputerAction(action_type=ActionType.SCREEN_CAPTURE)
        result = await self.executor.execute(action)
        # We don't return raw image data to the LLM directly, we return metadata or a path.
        # But for Phase 2, we just say it was captured.
        return {"status": "success", "message": "Screen captured successfully."}

class BrowserNavigateSchema(BaseModel):
    url: str = Field(..., description="The URL to navigate to.")

class BrowserNavigateTool(ComputerActionTool):
    @property
    def name(self) -> str: return "browser_navigate"
    
    @property
    def description(self) -> str: return "Navigates the browser to a specific URL."
    
    @property
    def input_schema(self) -> type[BaseModel]: return BrowserNavigateSchema
    
    @property
    def risk_level(self) -> RiskLevel: return RiskLevel.BROWSER_CONTROL
    
    async def execute(self, url: str, **kwargs: Any) -> Any:
        action = ComputerAction(action_type=ActionType.BROWSER_NAVIGATE, parameters={"url": url})
        return await self.executor.execute(action)
