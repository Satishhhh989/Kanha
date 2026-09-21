"""
Custom exception hierarchy for KAHNA.

This module defines all internal errors used throughout the application.
These errors should be caught at the API/CLI boundary and converted into
safe user-facing messages.
"""

class KahnaError(Exception):
    """Base exception for all KAHNA-specific errors."""
    pass

class ConfigurationError(KahnaError):
    """Raised when environment variables or config files are missing/invalid."""
    pass

class AIProviderError(KahnaError):
    """Raised when the AI provider (e.g., OpenRouter) fails to respond correctly."""
    pass

class ToolNotFoundError(KahnaError):
    """Raised when the AI requests a tool that does not exist in the registry."""
    pass

class ToolValidationError(KahnaError):
    """Raised when the arguments for a tool fail schema validation."""
    pass

class PermissionDeniedError(KahnaError):
    """Raised when the permission engine blocks a tool execution."""
    pass

class ToolExecutionError(KahnaError):
    """Raised when a tool execution fails internally."""
    pass

class PlatformError(KahnaError):
    """Raised when a platform-specific operation fails or is unsupported."""
    pass

class AgentLoopError(KahnaError):
    """Raised when the agent runtime encounters an unexpected state or infinite loop."""
    pass
