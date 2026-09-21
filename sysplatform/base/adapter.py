from typing import Protocol, runtime_checkable
from pydantic import BaseModel

class SystemInfo(BaseModel):
    """Normalized system information returned by platform adapters."""
    os_name: str
    os_version: str
    architecture: str
    hostname: str
    python_version: str
    cpu_cores: int
    memory_total_gb: float

@runtime_checkable
class PlatformAdapter(Protocol):
    """
    Protocol defining the contract for operating system interactions.
    
    Any platform-specific logic (macOS, Windows) must be implemented behind this interface.
    """
    
    def get_system_info(self) -> SystemInfo:
        """Returns normalized information about the host system."""
        ...
        
    def open_application(self, app_name: str) -> bool:
        """
        Attempts to open a standard graphical application by name.
        Returns True if the launch command succeeded, False otherwise.
        """
        ...

    def close_application(self, app_name: str) -> bool:
        """
        Attempts to close a standard graphical application by name.
        Returns True if the close command succeeded, False otherwise.
        """
        ...
