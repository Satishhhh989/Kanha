import platform
from core.computer.interfaces import ComputerController

def get_computer_controller() -> ComputerController:
    os_name = platform.system().lower()
    
    if os_name == "darwin":
        from sysplatform.macos.computer import MacOSComputerController
        return MacOSComputerController()
    elif os_name == "windows":
        from sysplatform.windows.computer import WindowsComputerController
        return WindowsComputerController()
    else:
        raise NotImplementedError(f"Computer control not supported on OS: {os_name}")
