import uuid
from typing import Dict, Any, Awaitable, Callable
from datetime import datetime, timedelta, timezone

class ConfirmationStatus:
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"

class ConfirmationRequest:
    def __init__(self, user_id: str, action: str, details: Dict[str, Any]):
        self.request_id = f"conf-{uuid.uuid4().hex[:8]}"
        self.user_id = user_id
        self.action = action
        self.details = details
        self.status = ConfirmationStatus.PENDING
        self.created_at = datetime.now(timezone.utc)
        self.expires_at = self.created_at + timedelta(minutes=5)
        # We store an asyncio.Future that will be set when the user responds
        import asyncio
        self.future = asyncio.Future()

    def is_expired(self) -> bool:
        if self.status != ConfirmationStatus.PENDING:
            return False
        return datetime.now(timezone.utc) > self.expires_at

class ConfirmationManager:
    """
    Manages expiring confirmation requests for high-risk remote actions.
    """
    def __init__(self):
        self._requests: Dict[str, ConfirmationRequest] = {}

    def create_request(self, user_id: str, action: str, details: Dict[str, Any]) -> ConfirmationRequest:
        req = ConfirmationRequest(user_id, action, details)
        self._requests[req.request_id] = req
        return req

    def get_request(self, request_id: str) -> ConfirmationRequest | None:
        req = self._requests.get(request_id)
        if req and req.is_expired():
            req.status = ConfirmationStatus.EXPIRED
            if not req.future.done():
                req.future.set_result(False)
        return req

    def resolve_request(self, request_id: str, approved: bool) -> bool:
        """Resolves a request and triggers the awaiting agent."""
        req = self.get_request(request_id)
        if not req or req.status != ConfirmationStatus.PENDING:
            return False
            
        req.status = ConfirmationStatus.APPROVED if approved else ConfirmationStatus.DENIED
        if not req.future.done():
            req.future.set_result(approved)
            
        return True

confirmation_manager = ConfirmationManager()
