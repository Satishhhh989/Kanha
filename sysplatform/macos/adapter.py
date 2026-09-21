import os
import platform
import subprocess
import sys
from sysplatform.base import PlatformAdapter, SystemInfo
from infrastructure.logging import get_logger

logger = get_logger("platform.macos")

class MacOSAdapter(PlatformAdapter):
    """macOS-specific platform implementation."""
    
    def get_system_info(self) -> SystemInfo:
        # Determine total memory using sysctl
        try:
            mem_bytes = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip()
            mem_gb = round(int(mem_bytes) / (1024 ** 3), 2)
        except Exception as e:
            logger.warning("Failed to get memory size", error=str(e))
            mem_gb = 0.0
            
        return SystemInfo(
            os_name="macOS",
            os_version=platform.mac_ver()[0],
            architecture=platform.machine(),
            hostname=platform.node(),
            python_version=sys.version.split()[0],
            cpu_cores=os.cpu_count() or 1,
            memory_total_gb=mem_gb
        )

    def open_application(self, app_name: str) -> bool:
        """Opens an application on macOS using the 'open -a' command."""
        logger.info("Opening application", app_name=app_name)
        try:
            subprocess.check_call(
                ["open", "-a", app_name],
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
        """Closes an application on macOS."""
        logger.info("Closing application", app_name=app_name)
        try:
            subprocess.run(["osascript", "-e", f'quit app "{app_name}"'], check=True, capture_output=True)
            return True
        except Exception:
            try:
                subprocess.run(["pkill", "-x", app_name], check=True, capture_output=True)
                return True
            except Exception as e:
                logger.error("Failed to close application", app_name=app_name, error=str(e))
                return False
