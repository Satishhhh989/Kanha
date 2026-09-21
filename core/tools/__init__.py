from .models import ToolCall, ToolResult
from .base import BaseTool
from .registry import ToolRegistry, tool_registry
from .system_tools import GetSystemInfoTool, GetCurrentTimeTool, OpenApplicationTool
from .fs_tools import ListDirectoryTool, ReadTextFileTool
from .computer_tools import ClickTool, TypeTextTool, ScreenCaptureTool, BrowserNavigateTool
from core.computer.factory import get_computer_controller

# Get a computer controller instance
controller = get_computer_controller()

# Register core system & fs tools
tool_registry.register(GetSystemInfoTool())
tool_registry.register(GetCurrentTimeTool())
tool_registry.register(OpenApplicationTool())
tool_registry.register(ListDirectoryTool())
tool_registry.register(ReadTextFileTool())

# Register Phase 2 computer tools
tool_registry.register(ClickTool(controller))
tool_registry.register(TypeTextTool(controller))
tool_registry.register(ScreenCaptureTool(controller))
tool_registry.register(BrowserNavigateTool(controller))

__all__ = [
    "ToolCall",
    "ToolResult",
    "BaseTool",
    "ToolRegistry",
    "tool_registry"
]
