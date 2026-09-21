import json
from typing import Any
from core.ai import OpenRouterProvider, SystemMessage, UserMessage, AssistantMessage, ToolMessage, Message
from core.tools import tool_registry
from core.security import permission_engine, PermissionDecision
from core.events import event_bus, BaseEvent, EventType
from core.errors import AgentLoopError, ToolExecutionError
from infrastructure.logging import get_logger
from .session import session_store, Session

logger = get_logger("core.agent.runtime")

SYSTEM_PROMPT = """You are KAHNA, a real-time voice-driven AI desktop assistant.
You speak directly out loud to the user through their computer speakers.

CRITICAL VOICE INSTRUCTIONS:
1. ALWAYS KEEP RESPONSES SHORT AND CRISP (1 to 2 sentences maximum).
2. Never produce long paragraphs, bulleted markdown lists, or verbose explanations unless specifically requested.
3. Be direct, friendly, and conversational.
4. If asked to perform an action (like opening an app or checking system status), execute the tool and confirm concisely in one sentence.
"""

import re
import datetime
from sysplatform import adapter
from core.tools.system_tools import OpenApplicationTool

class IntentMatcher:
    @staticmethod
    def match_fast_path(message: str) -> dict | None:
        """Checks if a message is a simple command that can bypass the LLM."""
        msg = message.strip().lower().rstrip(".!?")
        
        # Match 'open <app>' or 'launch <app>'
        app_match = re.match(r"^(?:open|launch)\s+(.+)", msg)
        if app_match:
            app_name = app_match.group(1).strip()
            return {"action": "open_app", "args": {"app_name": app_name}}
            
        # Match 'close <app>' or 'quit <app>'
        close_match = re.match(r"^(?:close|quit)\s+(.+)", msg)
        if close_match:
            app_name = close_match.group(1).strip()
            return {"action": "close_app", "args": {"app_name": app_name}}

        # Match time
        if any(t in msg for t in ["what time is it", "current time", "what is the time", "tell me the time"]):
            now = datetime.datetime.now().strftime("%I:%M %p")
            return {"action": "static_reply", "reply": f"The current time is {now}."}

        # Match identity
        if any(q in msg for q in ["who are you", "what is your name", "what's your name"]):
            return {"action": "static_reply", "reply": "I am KAHNA, your local desktop AI agent."}
            
        # Match help
        if msg in ["help", "what can you do", "commands"]:
            return {"action": "static_reply", "reply": "I can control your computer, open and close apps, take screenshots, manage remote access via Telegram, and assist you with tasks."}

        return None

class AgentRuntime:
    """
    The orchestrator of the KAHNA agent loop.
    """
    def __init__(self) -> None:
        self.ai = OpenRouterProvider()
        self.max_iterations = 5

    async def chat(self, session_id: str, message: str) -> str:
        """
        Processes a user message through the agent loop.
        """
        logger.info("Starting chat request", session_id=session_id)
        
        await event_bus.publish(BaseEvent(
            event_type=EventType.USER_MESSAGE_RECEIVED,
            session_id=session_id,
            payload={"message": message}
        ))
        
        # --- FAST PATH INTENT MATCHING ---
        fast_intent = IntentMatcher.match_fast_path(message)
        if fast_intent:
            logger.info("Fast-path intent matched", intent=fast_intent)
            action = fast_intent.get("action")
            if action == "open_app":
                app_name = fast_intent["args"]["app_name"]
                success = adapter.open_application(app_name)
                return f"✅ Opened {app_name}." if success else f"❌ Failed to open {app_name}."
            elif action == "close_app":
                app_name = fast_intent["args"]["app_name"]
                success = adapter.close_application(app_name)
                return f"✅ Closed {app_name}." if success else f"❌ Failed to close {app_name}."
            elif action == "static_reply":
                return fast_intent["reply"]
        
        session = session_store.get_session(session_id)
        if not session.messages:
            session.messages.append(SystemMessage(content=SYSTEM_PROMPT))
            
        session.messages.append(UserMessage(content=message))
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            
            await event_bus.publish(BaseEvent(
                event_type=EventType.AI_REQUEST_STARTED,
                session_id=session_id
            ))
            
            # 1. Call AI
            tools_schema = tool_registry.get_tool_schemas()
            try:
                ai_response = await self.ai.generate(session.messages, tools=tools_schema)
            except Exception as e:
                logger.error("AI Provider error", error=str(e))
                err_str = str(e).lower()
                if "401" in err_str or "unauthorized" in err_str:
                    return "OpenRouter rejected the API key (401 Unauthorized). Please verify your OPENROUTER_API_KEY in the .env file."
                elif "429" in err_str or "rate" in err_str:
                    return "The free AI model is currently experiencing high demand and rate limits on OpenRouter. Please try again in a moment."
                return f"AI provider error: {str(e)[:100]}. Direct commands like 'open Safari' are available offline."
            assistant_msg = ai_response.message
            session.messages.append(assistant_msg)
            
            await event_bus.publish(BaseEvent(
                event_type=EventType.AI_RESPONSE_RECEIVED,
                session_id=session_id,
                payload={"has_tool_calls": bool(assistant_msg.tool_calls)}
            ))
            
            # 2. Check if AI requested tools
            if not assistant_msg.tool_calls:
                session_store.save_session(session)
                return assistant_msg.content or ""
                
            # 3. Execute tools
            for tc in assistant_msg.tool_calls:
                await event_bus.publish(BaseEvent(
                    event_type=EventType.TOOL_CALL_STARTED,
                    session_id=session_id,
                    payload={"tool_name": tc.name}
                ))
                
                try:
                    tool = tool_registry.get(tc.name)
                    
                    # 4. Permission Engine Check
                    perm_result = permission_engine.authorize(tool.name, tool.risk_level)
                    if perm_result.decision != PermissionDecision.ALLOW:
                        if perm_result.decision == PermissionDecision.REQUIRE_CONFIRMATION and session_id.startswith("remote-"):
                            logger.info("Tool execution requires remote confirmation", tool=tool.name)
                            
                            # Publish an event that the Telegram adapter will catch to send the inline keyboard
                            user_id = session_id.split("-")[1]
                            from remote.sessions.confirmations import confirmation_manager
                            req = confirmation_manager.create_request(user_id, tool.name, tc.arguments)
                            
                            await event_bus.publish(BaseEvent(
                                event_type=EventType.TOOL_CALL_STARTED, # Reusing or we could create a new event type
                                session_id=session_id,
                                payload={"action": "REQUIRE_CONFIRMATION", "request_id": req.request_id, "tool_name": tool.name}
                            ))
                            
                            # Wait for the user to click the inline keyboard
                            approved = await req.future
                            
                            if not approved:
                                session.messages.append(ToolMessage(
                                    tool_call_id=tc.id,
                                    content=json.dumps({"error": "Permission Denied: User rejected the confirmation request."})
                                ))
                                continue
                            # If approved, execution proceeds to step 5
                        else:
                            logger.warning("Tool execution blocked by permission engine", tool=tool.name, reason=perm_result.reason)
                            session.messages.append(ToolMessage(
                                tool_call_id=tc.id,
                                content=json.dumps({"error": f"Permission Denied: {perm_result.reason}"})
                            ))
                            continue
                        
                    # 5. Execute
                    kwargs = tc.arguments
                    # We could strictly validate against tool.input_schema here
                    result = await tool.execute(**kwargs)
                    
                    await event_bus.publish(BaseEvent(
                        event_type=EventType.TOOL_CALL_COMPLETED,
                        session_id=session_id,
                        payload={"tool_name": tc.name, "success": True}
                    ))
                    
                    session.messages.append(ToolMessage(
                        tool_call_id=tc.id,
                        content=json.dumps(result)
                    ))
                    
                except Exception as e:
                    logger.error("Tool execution failed", tool=tc.name, error=str(e))
                    await event_bus.publish(BaseEvent(
                        event_type=EventType.TOOL_CALL_FAILED,
                        session_id=session_id,
                        payload={"tool_name": tc.name, "error": str(e)}
                    ))
                    session.messages.append(ToolMessage(
                        tool_call_id=tc.id,
                        content=json.dumps({"error": f"Execution failed: {str(e)}"})
                    ))

        # Reached max iterations
        raise AgentLoopError(f"Agent exceeded maximum iterations ({self.max_iterations}) without returning a final response.")

agent_runtime = AgentRuntime()
