import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from core.agent.runtime import AgentRuntime
from core.ai import AIResponse, AssistantMessage
from core.tools import ToolCall
from core.events import BaseEvent

@pytest.fixture
def mock_ai_provider():
    with patch("core.agent.runtime.OpenRouterProvider") as mock:
        yield mock

@pytest.mark.asyncio
async def test_agent_loop_with_tool_call(mock_ai_provider):
    # Setup mock to return a tool call on first iteration, then a final response
    mock_instance = mock_ai_provider.return_value
    
    # First response: call get_system_info
    call_msg = AssistantMessage(
        tool_calls=[ToolCall(id="call_1", name="get_system_info", arguments={})]
    )
    # Second response: final answer
    final_msg = AssistantMessage(content="The system info is retrieved.")
    
    mock_instance.generate = AsyncMock(side_effect=[
        AIResponse(message=call_msg),
        AIResponse(message=final_msg)
    ])
    
    agent = AgentRuntime()
    response = await agent.chat("test_session_id", "What is my system info?")
    
    assert response == "The system info is retrieved."
    assert mock_instance.generate.call_count == 2
