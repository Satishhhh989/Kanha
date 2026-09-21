import platform
from .base import PlatformAdapter, SystemInfo

def get_platform_adapter() -> PlatformAdapter:
    """Returns the appropriate PlatformAdapter for the host operating system."""
    system = platform.system().lower()
    if system == "darwin":
        from .macos.adapter import MacOSAdapter
        return MacOSAdapter()
    elif system == "windows":
        from .windows.adapter import WindowsAdapter
        return WindowsAdapter()
    else:
        # Fallback or raise error
        from core.errors import PlatformError
        raise PlatformError(f"Unsupported operating system: {system}")

# Eagerly initialize the adapter to fail fast if unsupported
adapter = get_platform_adapter()

__all__ = ["PlatformAdapter", "SystemInfo", "adapter", "get_platform_adapter"]
