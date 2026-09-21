import pytest
import asyncio
from core.events.bus import EventBus
from core.events.models import BaseEvent, EventType

@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    bus = EventBus()
    received_events = []
    
    async def handler(event: BaseEvent):
        received_events.append(event)
        
    bus.subscribe(EventType.SESSION_STARTED, handler)
    
    event = BaseEvent(event_type=EventType.SESSION_STARTED, session_id="test_session")
    await bus.publish(event)
    
    # allow tasks to complete
    await asyncio.sleep(0.01)
    
    assert len(received_events) == 1
    assert received_events[0].session_id == "test_session"
    assert received_events[0].event_type == EventType.SESSION_STARTED
