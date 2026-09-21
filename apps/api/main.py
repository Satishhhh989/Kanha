from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import uuid

from core.config import settings
from core.agent import agent_runtime
from core.errors import KahnaError
from core.events.bus import event_bus
from infrastructure.logging import get_logger, setup_logging
from apps.api.ws import ws_gateway
from remote.telegram.adapter import telegram_adapter

logger = get_logger("apps.api")

app = FastAPI(title="KAHNA Local API")

class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    response: str

@app.on_event("startup")
async def startup_event():
    setup_logging(level=settings.log_level, environment=settings.environment)
    logger.info("Starting KAHNA API server", host=settings.host, port=settings.port)
    ws_gateway.start(event_bus)
    
    import asyncio
    import os
    services = os.environ.get("KAHNA_SERVICES", "api,telegram").split(",")
    
    if "voice" in services:
        from core.voice.factory import voice_manager
        logger.info("Starting Voice Manager service")
        asyncio.create_task(voice_manager.start())
        
    if "telegram" in services:
        logger.info("Starting Telegram Adapter service")
        asyncio.create_task(telegram_adapter.start())

@app.on_event("shutdown")
async def shutdown_event():
    ws_gateway.stop()
    import os
    services = os.environ.get("KAHNA_SERVICES", "api,telegram").split(",")
    
    if "voice" in services:
        from core.voice.factory import voice_manager
        await voice_manager.stop()
        
    if "telegram" in services:
        await telegram_adapter.stop()

@app.exception_handler(KahnaError)
async def kahna_exception_handler(request: Request, exc: KahnaError):
    logger.error("API error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "type": type(exc).__name__},
    )

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    try:
        response_text = await agent_runtime.chat(session_id, req.message)
        return ChatResponse(session_id=session_id, response=response_text)
    except Exception as e:
        logger.error("Unhandled exception during chat", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_gateway.handle_connection(websocket)

@app.get("/health")
async def health_endpoint():
    return {"status": "ok"}

def run_server():
    uvicorn.run(
        "apps.api.main:app", 
        host=settings.host, 
        port=settings.port, 
        reload=(settings.environment == "development")
    )
