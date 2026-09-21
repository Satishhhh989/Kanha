import asyncio
import uuid
import json
from aiortc import RTCSessionDescription
from infrastructure.logging import get_logger
from remote.streaming.webrtc import stream_manager
from infrastructure.logging.audit import audit_logger

logger = get_logger("core.remote.signaling")

class SignalingManager:
    """
    Manages WebRTC signaling and active session tokens.
    In a full production deployment, this would connect to an outbound WebSocket Relay.
    For this implementation, it manages temporary session tokens that can be exchanged
    via the local API or a configured relay.
    """
    def __init__(self):
        self._active_tokens = {}
        
    def generate_token(self, user_id: str) -> str:
        """Generates a short-lived secure token for WebRTC signaling."""
        token = f"kahna_rtc_{uuid.uuid4().hex}"
        # Store token with user_id and expiration
        self._active_tokens[token] = {
            "user_id": user_id,
            "created_at": asyncio.get_event_loop().time()
        }
        return token
        
    def validate_token(self, token: str) -> str | None:
        """Validates a token and returns the user_id if valid."""
        data = self._active_tokens.get(token)
        if not data:
            return None
            
        # 10 minute expiration
        if asyncio.get_event_loop().time() - data["created_at"] > 600:
            del self._active_tokens[token]
            return None
            
        return data["user_id"]
        
    def consume_token(self, token: str):
        if token in self._active_tokens:
            del self._active_tokens[token]

    async def handle_offer(self, token: str, offer_sdp: str, offer_type: str) -> dict:
        """
        Handles an incoming WebRTC SDP offer using a valid token,
        returns the SDP answer.
        """
        user_id = self.validate_token(token)
        if not user_id:
            raise ValueError("Invalid or expired session token.")
            
        # Consume token so it can't be reused for a new connection
        self.consume_token(token)
        
        session_id = f"stream_{uuid.uuid4().hex[:8]}"
        session = stream_manager.create_session(session_id)
        
        audit_logger.log_screen_session_started(session_id, user_id)
        
        offer = RTCSessionDescription(sdp=offer_sdp, type=offer_type)
        await session.pc.setRemoteDescription(offer)
        
        answer = await session.pc.createAnswer()
        await session.pc.setLocalDescription(answer)
        
        return {
            "sdp": session.pc.localDescription.sdp,
            "type": session.pc.localDescription.type,
            "session_id": session_id
        }

signaling_manager = SignalingManager()
