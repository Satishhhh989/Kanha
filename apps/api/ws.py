import asyncio
import json
from typing import List, Callable, Any
from fastapi import WebSocket, WebSocketDisconnect

from core.events.models import BaseEvent
from core.events.bus import EventBus
from infrastructure.logging import get_logger

logger = get_logger("apps.api.ws")

class WebSocketGateway:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._subscription_id: str | None = None
        self._event_bus: EventBus | None = None

    def start(self, event_bus: EventBus):
        self._event_bus = event_bus
        self._subscription_id = event_bus.subscribe_all(self._handle_bus_event)
        logger.info("WebSocketGateway started and subscribed to EventBus")

    def stop(self):
        if self._event_bus and self._subscription_id:
            self._event_bus.unsubscribe(self._subscription_id)
        logger.info("WebSocketGateway stopped")

    async def handle_connection(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.debug("WebSocket client connected")
        
        try:
            while True:
                data = await websocket.receive_text()
                # We could route UI commands back to KAHNA here if needed.
                # For now, KAHNA is the primary driver, UI is mostly a visualizer,
                # but we could handle settings changes or manual interactions.
                logger.debug("Received from UI", data=data)
        except WebSocketDisconnect:
            logger.debug("WebSocket client disconnected")
            self.active_connections.remove(websocket)
        except Exception as e:
            logger.error("WebSocket error", error=str(e))
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def _handle_bus_event(self, event: BaseEvent):
        # Broadcast all events to UI
        if not self.active_connections:
            return
            
        event_json = event.model_dump_json()
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(event_json)
            except Exception as e:
                logger.error("Failed to send event to WebSocket", error=str(e))
                disconnected.append(connection)
                
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

ws_gateway = WebSocketGateway()
