import json
from typing import Any, Protocol, runtime_checkable
import httpx
from core.config import settings
from core.errors import AIProviderError
from core.tools import ToolCall
from infrastructure.logging import get_logger
from .models import Message, SystemMessage, UserMessage, AssistantMessage, ToolMessage, AIResponse

logger = get_logger("core.ai")

@runtime_checkable
class AIProvider(Protocol):
    async def generate(self, messages: list[Message], tools: list[dict[str, Any]] | None = None) -> AIResponse:
        ...

class OpenRouterProvider(AIProvider):
    def __init__(self) -> None:
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://127.0.0.1",
            "X-Title": "KAHNA Local Agent"
        }

    def _format_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        formatted = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                formatted.append({"role": "system", "content": msg.content})
            elif isinstance(msg, UserMessage):
                formatted.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AssistantMessage):
                payload: dict[str, Any] = {"role": "assistant"}
                if msg.content:
                    payload["content"] = msg.content
                if msg.tool_calls:
                    payload["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments)
                            }
                        }
                        for tc in msg.tool_calls
                    ]
                formatted.append(payload)
            elif isinstance(msg, ToolMessage):
                formatted.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "content": msg.content
                })
        return formatted

    async def generate(self, messages: list[Message], tools: list[dict[str, Any]] | None = None) -> AIResponse:
        logger.debug("Generating response from OpenRouter", model=self.model, message_count=len(messages))
        
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._format_messages(messages)
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        models_to_try = [self.model]
        for fb in ["nex-agi/nex-n2.5-pro:free", "nex-agi/nex-n2.5-mini:free", "inclusionai/ling-3.0-flash-vl:free"]:
            if fb not in models_to_try:
                models_to_try.append(fb)

        last_error = None
        data = None

        async with httpx.AsyncClient() as client:
            for current_model in models_to_try:
                payload["model"] = current_model
                try:
                    response = await client.post(
                        self.base_url,
                        headers=self.headers,
                        json=payload,
                        timeout=httpx.Timeout(45.0)
                    )
                    if response.status_code == 200:
                        data = response.json()
                        break
                    elif response.status_code in (429, 500, 502, 503):
                        logger.warning(f"Model {current_model} returned {response.status_code}, trying fallback...")
                        last_error = f"Model {current_model} returned {response.status_code}: {response.text[:100]}"
                        continue
                    else:
                        response.raise_for_status()
                except httpx.HTTPError as e:
                    last_error = str(e)
                    logger.warning(f"HTTP error on {current_model}: {e}, trying fallback...")
                    continue
                except Exception as e:
                    last_error = str(e)
                    logger.error("Unexpected error from OpenRouter", error=str(e))
                    raise AIProviderError(f"Unexpected OpenRouter error: {e}")

        if data is None:
            raise AIProviderError(f"OpenRouter models failed or rate-limited: {last_error}")

        # Parse response
        try:
            choice = data["choices"][0]["message"]
            content = choice.get("content")
            raw_tool_calls = choice.get("tool_calls", [])
            
            tool_calls = []
            if raw_tool_calls:
                for tc in raw_tool_calls:
                    if tc["type"] == "function":
                        tool_calls.append(ToolCall(
                            id=tc["id"],
                            name=tc["function"]["name"],
                            arguments=json.loads(tc["function"]["arguments"])
                        ))
                        
            assistant_message = AssistantMessage(
                content=content,
                tool_calls=tool_calls if tool_calls else None
            )
            
            return AIResponse(message=assistant_message, raw_response=data)
            
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error("Failed to parse OpenRouter response", error=str(e), response=data)
            raise AIProviderError(f"Malformed response from OpenRouter: {e}")
