from core.config import settings
from infrastructure.logging.audit import audit_logger
from infrastructure.logging import get_logger

logger = get_logger("remote.authentication.identity")

class AuthenticationManager:
    """
    Handles authentication and identity verification for remote access.
    """
    
    def __init__(self):
        self.allowed_user_id = settings.telegram_allowed_user_id
        self.device_id = settings.kahna_device_id
        self.device_secret = settings.kahna_device_secret

    def authenticate_telegram_user(self, user_id: int | str) -> bool:
        """
        Validates if the provided Telegram User ID is explicitly authorized.
        Supports single ID or comma-separated list of IDs in TELEGRAM_ALLOWED_USER_ID.
        """
        user_id_str = str(user_id).strip()
        allowed = settings.telegram_allowed_user_id
        
        if not allowed:
            logger.warning(
                f"\n\n==========================================\n"
                f"UNAUTHORIZED TELEGRAM ACCESS ATTEMPT\n"
                f"User ID: {user_id_str}\n"
                f"To allow this user, add to .env:\n"
                f"TELEGRAM_ALLOWED_USER_ID={user_id_str}\n"
                f"==========================================\n"
            )
            # If no allowed user is configured, we reject ALL remote access.
            audit_logger.log_remote_login(user_id_str, success=False, reason="No allowed user configured")
            return False

        allowed_ids = [uid.strip() for uid in str(allowed).split(",") if uid.strip()]
        if user_id_str in allowed_ids:
            audit_logger.log_remote_login(user_id_str, success=True)
            return True
            
        audit_logger.log_remote_login(user_id_str, success=False, reason="User ID not allowed")
        return False
        
    def validate_device_secret(self, secret: str) -> bool:
        """
        Validates the device secret (used for WebRTC signaling or advanced pairings).
        """
        if not secret or not self.device_secret:
            return False
        return secret == self.device_secret

# Global singleton
auth_manager = AuthenticationManager()
