import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from core.config import settings

class AuditLogger:
    """
    Dedicated logger for security and remote events.
    Writes strictly to a local audit.log file, ensuring sensitive data is not leaked
    but security events are recorded.
    """
    def __init__(self, log_dir: str = "logs"):
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        self.log_file = os.path.join(log_dir, "audit.log")
        
        self.logger = logging.getLogger("kahna.audit")
        self.logger.setLevel(logging.INFO)
        
        # Prevent propagation to the main logger to avoid stdout leakage
        self.logger.propagate = False
        
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file, encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _log_event(self, event_name: str, **kwargs):
        """Format and log an audit event."""
        # Sanitize arguments: Never log explicit tokens/secrets
        safe_kwargs = {k: v for k, v in kwargs.items() if 'token' not in k.lower() and 'secret' not in k.lower()}
        
        details = ", ".join(f"{k}={v}" for k, v in safe_kwargs.items())
        msg = f"EVENT={event_name} | {details}"
        self.logger.info(msg)

    def log_remote_login(self, user_id: str, success: bool, reason: str = ""):
        self._log_event("REMOTE_LOGIN", user_id=user_id, success=success, reason=reason)

    def log_remote_command(self, user_id: str, command: str):
        self._log_event("REMOTE_COMMAND", user_id=user_id, command=command)

    def log_permission_evaluated(self, user_id: str, tool: str, decision: str, reason: str = ""):
        self._log_event("PERMISSION_EVALUATED", user_id=user_id, tool=tool, decision=decision, reason=reason)

    def log_confirmation_requested(self, user_id: str, action: str):
        self._log_event("CONFIRMATION_REQUESTED", user_id=user_id, action=action)

    def log_confirmation_resolved(self, user_id: str, action: str, approved: bool):
        self._log_event("CONFIRMATION_RESOLVED", user_id=user_id, action=action, approved=approved)

    def log_screen_session_started(self, session_id: str, user_id: str):
        self._log_event("SCREEN_SESSION_STARTED", session_id=session_id, user_id=user_id)

    def log_screen_session_ended(self, session_id: str, reason: str = ""):
        self._log_event("SCREEN_SESSION_ENDED", session_id=session_id, reason=reason)

# Global singleton
audit_logger = AuditLogger()
