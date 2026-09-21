from typing import Any
from .base import BaseTool
from core.errors import ToolNotFoundError

class ToolRegistry:
    """
    Central registry for all available KAHNA tools.
    """
    
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        
    def register(self, tool: BaseTool) -> None:
        """Registers a tool."""
        self._tools[tool.name] = tool
        
    def unregister(self, tool_name: str) -> None:
        """Unregisters a tool."""
        if tool_name in self._tools:
            del self._tools[tool_name]
            
    def get(self, tool_name: str) -> BaseTool:
        """Retrieves a tool by name or raises ToolNotFoundError."""
        if tool_name not in self._tools:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found in registry.")
        return self._tools[tool_name]
        
    def list_tools(self) -> list[BaseTool]:
        """Returns a list of all registered tools."""
        return list(self._tools.values())
        
    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """
        Returns JSON-schema representation of tools suitable for AI providers (e.g. OpenAI format).
        """
        schemas = []
        for tool in self._tools.values():
            schema = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema.model_json_schema()
                }
            }
            schemas.append(schema)
        return schemas

# Global tool registry
tool_registry = ToolRegistry()
