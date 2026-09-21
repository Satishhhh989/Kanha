from typing import Any
from .models import RiskLevel, PermissionDecision, PermissionResult
from infrastructure.logging import get_logger

logger = get_logger("core.security")

class PermissionEngine:
    """
    Evaluates whether a tool execution is allowed based on its risk level and context.
    """
    
    def authorize(self, tool_name: str, risk_level: RiskLevel, context: dict[str, Any] | None = None) -> PermissionResult:
        """
        Determines the permission decision for a given tool.
        
        Phase 1 Default Policy:
        - READ_ONLY and LOW are ALLOWED.
        - MEDIUM and HIGH are REQUIRE_CONFIRMATION (or ALLOWED for specific safe tools).
        - CRITICAL is explicitly DENIED.
        """
        
        logger.debug("Authorizing tool execution", tool=tool_name, risk_level=risk_level.value)
        
        if risk_level in (RiskLevel.READ_ONLY, RiskLevel.COMPUTER_INTERACTION, RiskLevel.APPLICATION_CONTROL, RiskLevel.BROWSER_CONTROL):
            return PermissionResult(decision=PermissionDecision.ALLOW)
            
        if risk_level == RiskLevel.DESTRUCTIVE:
            return PermissionResult(
                decision=PermissionDecision.DENY, 
                reason="DESTRUCTIVE operations are forbidden in Phase 2."
            )
            
        return PermissionResult(
            decision=PermissionDecision.REQUIRE_CONFIRMATION,
            reason="Tool requires explicit user confirmation due to risk level."
        )

# Global singleton
permission_engine = PermissionEngine()
