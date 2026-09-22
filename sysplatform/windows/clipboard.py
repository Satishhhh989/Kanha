import sys
import subprocess
from core.computer.interfaces import ClipboardController
from infrastructure.logging import get_logger

logger = get_logger("sysplatform.windows.clipboard")

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

class WindowsClipboardController(ClipboardController):
    """Windows clipboard controller using Win32 API and PowerShell fallback."""

    async def read_clipboard(self) -> str:
        if sys.platform == "win32":
            import ctypes
            try:
                if ctypes.windll.user32.OpenClipboard(None):
                    try:
                        handle = ctypes.windll.user32.GetClipboardData(CF_UNICODETEXT)
                        if handle:
                            ptr = ctypes.windll.kernel32.GlobalLock(handle)
                            if ptr:
                                text = ctypes.c_wchar_p(ptr).value or ""
                                ctypes.windll.kernel32.GlobalUnlock(handle)
                                logger.debug("Read clipboard via Win32")
                                return text
                        return ""
                    finally:
                        ctypes.windll.user32.CloseClipboard()
            except Exception as e:
                logger.debug("Win32 clipboard read failed, trying PowerShell", error=str(e))

        # Fallback using PowerShell
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug("Read clipboard via PowerShell")
            return res.stdout.rstrip("\r\n")
        except Exception as e:
            logger.error("Failed to read clipboard", error=str(e))
            return ""

    async def write_clipboard(self, text: str) -> None:
        if sys.platform == "win32":
            import ctypes
            try:
                if ctypes.windll.user32.OpenClipboard(None):
                    try:
                        ctypes.windll.user32.EmptyClipboard()
                        encoded = text.encode("utf-16-le") + b"\x00\x00"
                        h_mem = ctypes.windll.kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
                        if h_mem:
                            ptr = ctypes.windll.kernel32.GlobalLock(h_mem)
                            if ptr:
                                ctypes.memmove(ptr, encoded, len(encoded))
                                ctypes.windll.kernel32.GlobalUnlock(h_mem)
                                ctypes.windll.user32.SetClipboardData(CF_UNICODETEXT, h_mem)
                                logger.debug("Wrote to clipboard via Win32")
                                return
                    finally:
                        ctypes.windll.user32.CloseClipboard()
            except Exception as e:
                logger.debug("Win32 clipboard write failed, trying PowerShell", error=str(e))

        # Fallback using PowerShell
        try:
            process = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", "$input | Set-Clipboard"],
                stdin=subprocess.PIPE
            )
            process.communicate(input=text.encode("utf-8"))
            logger.debug("Wrote to clipboard via PowerShell")
        except Exception as e:
            logger.error("Failed to write to clipboard", error=str(e))

    async def clear_clipboard(self) -> None:
        await self.write_clipboard("")
