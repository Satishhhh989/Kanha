import pytest
from core.security.engine import PermissionEngine
from core.security.models import RiskLevel, PermissionDecision

def test_permission_engine():
    engine = PermissionEngine()
    
    # Read only should be allowed
    result = engine.authorize("get_system_info", RiskLevel.READ_ONLY)
    assert result.decision == PermissionDecision.ALLOW
    
    # Computer interaction should be allowed
    result = engine.authorize("move_mouse", RiskLevel.COMPUTER_INTERACTION)
    assert result.decision == PermissionDecision.ALLOW
    
    # Destructive should be denied
    result = engine.authorize("delete_file", RiskLevel.DESTRUCTIVE)
    assert result.decision == PermissionDecision.DENY
    
    # Sensitive data should require confirmation
    result = engine.authorize("read_clipboard", RiskLevel.SENSITIVE_DATA)
    assert result.decision == PermissionDecision.REQUIRE_CONFIRMATION
