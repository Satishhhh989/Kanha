import os
import platform
import subprocess
import sys
from sysplatform.base import PlatformAdapter, SystemInfo
from infrastructure.logging import get_logger

logger = get_logger("platform.windows")

class WindowsAdapter(PlatformAdapter):
    """Windows-specific platform implementation."""
    
    def get_system_info(self) -> SystemInfo:
        # Determine total memory using ctypes on Windows
        mem_gb = 0.0
        try:
            import ctypes
            class MemoryStatusEx(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MemoryStatusEx()
            stat.dwLength = ctypes.sizeof(MemoryStatusEx)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            mem_gb = round(stat.ullTotalPhys / (1024 ** 3), 2)
        except Exception as e:
            logger.warning("Failed to get memory size", error=str(e))
            
        return SystemInfo(
            os_name="Windows",
            os_version=platform.version(),
            architecture=platform.machine(),
            hostname=platform.node(),
            python_version=sys.version.split()[0],
            cpu_cores=os.cpu_count() or 1,
            memory_total_gb=mem_gb
        )

    def open_application(self, app_name: str) -> bool:
        """Opens an application on Windows."""
        logger.info("Opening application", app_name=app_name)
        try:
            # Using start to launch an executable or registered application
            subprocess.check_call(
                ["cmd", "/c", "start", "", app_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except subprocess.CalledProcessError:
            logger.error("Failed to open application", app_name=app_name)
            return False
        except Exception as e:
            logger.error("Unexpected error opening application", app_name=app_name, error=str(e))
            return False

    def close_application(self, app_name: str) -> bool:
        """Closes an application on Windows using taskkill."""
        logger.info("Closing application", app_name=app_name)
        try:
            exe_name = app_name if app_name.lower().endswith(".exe") else f"{app_name}.exe"
            subprocess.run(["taskkill", "/F", "/IM", exe_name], check=True, capture_output=True)
            return True
        except Exception as e:
            logger.error("Failed to close application on Windows", app_name=app_name, error=str(e))
            return False
