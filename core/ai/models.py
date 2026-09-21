from typing import Any, Literal
from pydantic import BaseModel, Field
from core.tools import ToolCall

class Message(BaseModel):
    """Base class for messages in a conversation."""
    role: str
    content: str | None = None

class SystemMessage(Message):
    role: Literal["system"] = "system"

class UserMessage(Message):
    role: Literal["user"] = "user"

class AssistantMessage(Message):
    role: Literal["assistant"] = "assistant"
    tool_calls: list[ToolCall] | None = None

class ToolMessage(Message):
    role: Literal["tool"] = "tool"
    tool_call_id: str
    
class AIResponse(BaseModel):
    """Normalized response from an AI provider."""
    message: AssistantMessage
    raw_response: dict[str, Any] | None = Field(default=None, exclude=True)
