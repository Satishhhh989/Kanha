from typing import Any
from pydantic import BaseModel, Field

class ToolCall(BaseModel):
    """
    Represents a tool invocation requested by the AI.
    """
    id: str
    name: str
    arguments: dict[str, Any]

class ToolResult(BaseModel):
    """
    Represents the outcome of a tool execution.
    """
    tool_call_id: str
    success: bool
    output: Any | None = None
    error: str | None = None
