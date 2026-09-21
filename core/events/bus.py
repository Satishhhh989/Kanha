import asyncio
from typing import Callable, Awaitable
from collections import defaultdict
from .models import BaseEvent, EventType
from infrastructure.logging import get_logger

logger = get_logger("core.events.bus")

EventHandler = Callable[[BaseEvent], Awaitable[None]]

class EventBus:
    """
    Lightweight internal event bus for KAHNA.
    
    Routes events to registered asynchronous handlers.
    """
    
    def __init__(self) -> None:
        self._subscribers: dict[EventType, list[EventHandler]] = defaultdict(list)
        self._all_subscribers: list[EventHandler] = []
    
    def subscribe(self, event_type: EventType, handler: EventHandler) -> EventHandler:
        """Registers a handler for a specific event type."""
        self._subscribers[event_type].append(handler)
        logger.debug("Event handler subscribed", event_type=event_type.value, handler=handler.__name__)
        return handler

    def subscribe_all(self, handler: EventHandler) -> EventHandler:
        """Registers a handler for all events."""
        self._all_subscribers.append(handler)
        logger.debug("Global event handler subscribed", handler=handler.__name__)
        return handler
        
    def unsubscribe(self, handler: EventHandler) -> None:
        """Removes a handler from all subscriptions."""
        if handler in self._all_subscribers:
            self._all_subscribers.remove(handler)
        for event_type, handlers in self._subscribers.items():
            if handler in handlers:
                handlers.remove(handler)

    def emit(self, event: BaseEvent) -> None:
        """Publishes an event synchronously by scheduling tasks on the running event loop."""
        handlers = self._subscribers.get(event.event_type, [])
        all_handlers = self._all_subscribers
        if not handlers and not all_handlers:
            return
        
        logger.debug("Publishing event", event_type=event.event_type.value, session_id=event.session_id)
        try:
            loop = asyncio.get_running_loop()
            for handler in handlers:
                loop.create_task(self._safe_invoke(handler, event))
            for handler in all_handlers:
                loop.create_task(self._safe_invoke(handler, event))
        except RuntimeError:
            pass

    async def publish(self, event: BaseEvent) -> None:
        """Publishes an event to all registered handlers asynchronously."""
        self.emit(event)

    async def _safe_invoke(self, handler: EventHandler, event: BaseEvent) -> None:
        """Safely invokes an event handler, catching any exceptions."""
        try:
            await handler(event)
        except Exception as e:
            logger.error(
                "Event handler failed", 
                event_type=event.event_type.value, 
                handler=handler.__name__, 
                error=str(e),
                exc_info=True
            )

# Global event bus
event_bus = EventBus()
