from enum import Enum
from pydantic import BaseModel

class RiskLevel(str, Enum):
    """
    Categorizes the potential impact of a tool.
    """
    READ_ONLY = "READ_ONLY" # Screen dimension, list apps, get mouse pos
    COMPUTER_INTERACTION = "COMPUTER_INTERACTION" # Move mouse, scroll
    APPLICATION_CONTROL = "APPLICATION_CONTROL" # Open/close apps
    BROWSER_CONTROL = "BROWSER_CONTROL" # Browser navigation
    FILE_WRITE = "FILE_WRITE" # Writing safe files
    SENSITIVE_DATA = "SENSITIVE_DATA" # Clipboard read/write, screen capture
    DESTRUCTIVE = "DESTRUCTIVE" # Delete file, close critical apps
    UNKNOWN = "UNKNOWN"

class PermissionDecision(str, Enum):
    """
    The result of a permission evaluation.
    """
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_CONFIRMATION = "REQUIRE_CONFIRMATION"

class PermissionResult(BaseModel):
    decision: PermissionDecision
    reason: str | None = None
