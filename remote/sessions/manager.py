import uuid
from typing import Dict

class RemoteSessionManager:
    """
    Manages session mapping for Telegram users to KAHNA's Agent Runtime.
    Ensures each user gets an isolated conversation context.
    """
    
    def __init__(self):
        # Maps user_id -> kahna_session_id
        self._active_sessions: Dict[str, str] = {}
        
    def get_or_create_session(self, user_id: str) -> str:
        """Returns the active session ID for a remote user, or creates one."""
        if user_id not in self._active_sessions:
            self._active_sessions[user_id] = f"remote-{user_id}-{uuid.uuid4().hex[:8]}"
        return self._active_sessions[user_id]
        
    def reset_session(self, user_id: str):
        """Clears the active session for a remote user."""
        if user_id in self._active_sessions:
            del self._active_sessions[user_id]

# Global singleton
remote_sessions = RemoteSessionManager()
