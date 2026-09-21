import asyncio
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from core.computer.models import ComputerAction, TaskState
from core.computer.executor import ActionExecutor
from core.events import BaseEvent, EventType, event_bus
from infrastructure.logging import get_logger

logger = get_logger("core.agent.task")

class TaskContext(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    actions: List[ComputerAction]
    current_step: int = 0
    state: TaskState = TaskState.PENDING
    results: List[Dict[str, Any]] = Field(default_factory=list)
    max_retries: int = 2

class TaskExecutor:
    """Executes a sequence of ComputerActions with retries and cancellation support."""
    
    def __init__(self, action_executor: ActionExecutor):
        self.action_executor = action_executor
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._task_contexts: Dict[str, TaskContext] = {}

    async def execute_task(self, session_id: str, actions: List[ComputerAction]) -> TaskContext:
        """Starts executing a task in the background."""
        context = TaskContext(session_id=session_id, actions=actions)
        self._task_contexts[context.task_id] = context
        
        # Fire background task
        task = asyncio.create_task(self._run_task_loop(context))
        self._active_tasks[context.task_id] = task
        
        # We don't await the task here, we return the context so the agent runtime can 
        # track it if necessary, but typically we might just await it directly if synchronous 
        # execution is desired by the runtime. For now, let's await it to provide sequential flow.
        await task
        return context

    async def cancel_task(self, task_id: str) -> bool:
        """Cancels a running task."""
        if task_id in self._active_tasks:
            self._active_tasks[task_id].cancel()
            context = self._task_contexts.get(task_id)
            if context:
                context.state = TaskState.CANCELLED
            logger.info("Cancelled task", task_id=task_id)
            return True
        return False

    async def _run_task_loop(self, context: TaskContext) -> None:
        context.state = TaskState.RUNNING
        await event_bus.publish(BaseEvent(
            event_type=EventType.AGENT_TASK_STARTED,
            session_id=context.session_id,
            payload={"task_id": context.task_id, "total_steps": len(context.actions)}
        ))
        
        try:
            for i, action in enumerate(context.actions):
                context.current_step = i
                success = False
                attempts = 0
                
                while not success and attempts <= context.max_retries:
                    attempts += 1
                    try:
                        # Ensure we check for cancellation
                        await asyncio.sleep(0)
                        
                        await event_bus.publish(BaseEvent(
                            event_type=EventType.COMPUTER_ACTION_STARTED,
                            session_id=context.session_id,
                            payload={"task_id": context.task_id, "action_id": action.action_id}
                        ))
                        
                        result = await self.action_executor.execute(action)
                        context.results.append(result)
                        success = True
                        
                        await event_bus.publish(BaseEvent(
                            event_type=EventType.COMPUTER_ACTION_COMPLETED,
                            session_id=context.session_id,
                            payload={"task_id": context.task_id, "action_id": action.action_id}
                        ))
                        
                    except asyncio.CancelledError:
                        logger.info("Task loop cancelled", task_id=context.task_id)
                        raise
                    except Exception as e:
                        logger.warning(
                            "Action failed, retrying", 
                            task_id=context.task_id, 
                            action_id=action.action_id, 
                            attempt=attempts, 
                            error=str(e)
                        )
                        if attempts > context.max_retries:
                            raise Exception(f"Action failed after {context.max_retries} retries: {str(e)}")
                            
                        await event_bus.publish(BaseEvent(
                            event_type=EventType.TASK_RECOVERY_STARTED,
                            session_id=context.session_id,
                            payload={"task_id": context.task_id, "action_id": action.action_id, "attempt": attempts}
                        ))
                        # Wait before retry
                        await asyncio.sleep(1.0)
                        
            context.state = TaskState.COMPLETED
            await event_bus.publish(BaseEvent(
                event_type=EventType.AGENT_TASK_COMPLETED,
                session_id=context.session_id,
                payload={"task_id": context.task_id, "results": context.results}
            ))
            
        except asyncio.CancelledError:
            context.state = TaskState.CANCELLED
            # Bubble up cancellation
        except Exception as e:
            context.state = TaskState.FAILED
            logger.error("Task failed", task_id=context.task_id, error=str(e))
            await event_bus.publish(BaseEvent(
                event_type=EventType.COMPUTER_ACTION_FAILED,
                session_id=context.session_id,
                payload={"task_id": context.task_id, "error": str(e)}
            ))
        finally:
            if context.task_id in self._active_tasks:
                del self._active_tasks[context.task_id]
