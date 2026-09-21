from typing import Protocol, Any, Dict, Optional
from core.computer.models import ComputerAction, ActionType
from core.computer.interfaces import ComputerController
from infrastructure.logging import get_logger

logger = get_logger("core.computer.verification")

class VerificationStrategy(Protocol):
    async def verify(self, action: ComputerAction, controller: ComputerController) -> bool:
        """Returns True if the action is verified as successful, False otherwise."""
        ...

class OpenApplicationVerifier:
    async def verify(self, action: ComputerAction, controller: ComputerController) -> bool:
        target_app = action.target
        if not target_app:
            return False
            
        logger.debug("Verifying OPEN_APPLICATION", target=target_app)
        return await controller.application.is_application_running(target_app)

class CloseApplicationVerifier:
    async def verify(self, action: ComputerAction, controller: ComputerController) -> bool:
        target_app = action.target
        if not target_app:
            return False
            
        logger.debug("Verifying CLOSE_APPLICATION", target=target_app)
        is_running = await controller.application.is_application_running(target_app)
        return not is_running

class FocusWindowVerifier:
    async def verify(self, action: ComputerAction, controller: ComputerController) -> bool:
        target_window_id = action.target
        if not target_window_id:
            return False
            
        logger.debug("Verifying FOCUS_WINDOW", target=target_window_id)
        active_window = await controller.window.get_active_window()
        
        if not active_window:
            return False
            
        # Implementation depends on how window IDs are structured in get_active_window
        return active_window.get("id") == target_window_id

class ClipboardWriteVerifier:
    async def verify(self, action: ComputerAction, controller: ComputerController) -> bool:
        text_written = action.parameters.get("text")
        if text_written is None:
            return False
            
        logger.debug("Verifying CLIPBOARD_WRITE")
        current_clipboard = await controller.clipboard.read_clipboard()
        return current_clipboard == text_written

class BrowserNavigateVerifier:
    async def verify(self, action: ComputerAction, controller: ComputerController) -> bool:
        target_url = action.parameters.get("url")
        if not target_url:
            return False
            
        logger.debug("Verifying BROWSER_NAVIGATE", target=target_url)
        current_url = await controller.browser.get_current_url()
        # Normalization might be needed (e.g. ignoring trailing slashes)
        return target_url.strip('/') in current_url.strip('/')


class VerificationEngine:
    """Routes actions to their respective verification strategies."""
    
    def __init__(self):
        self._strategies: Dict[ActionType, VerificationStrategy] = {
            ActionType.OPEN_APPLICATION: OpenApplicationVerifier(),
            ActionType.CLOSE_APPLICATION: CloseApplicationVerifier(),
            ActionType.FOCUS_WINDOW: FocusWindowVerifier(),
            ActionType.CLIPBOARD_WRITE: ClipboardWriteVerifier(),
            ActionType.BROWSER_NAVIGATE: BrowserNavigateVerifier(),
        }
        
    async def verify_action(self, action: ComputerAction, controller: ComputerController) -> bool:
        strategy = self._strategies.get(action.action_type)
        
        if not strategy:
            # If no strategy is explicitly defined, we assume success or "unknown but proceeding".
            # The prompt says: "Use the cheapest reliable verification method first."
            logger.debug("No verification strategy defined, assuming success", action_type=action.action_type)
            return True
            
        try:
            return await strategy.verify(action, controller)
        except Exception as e:
            logger.error("Verification failed with error", error=str(e), action_type=action.action_type)
            return False

# Global verification engine
verification_engine = VerificationEngine()
