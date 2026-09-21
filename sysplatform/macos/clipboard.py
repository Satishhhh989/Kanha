import subprocess
from core.computer.interfaces import ClipboardController
from infrastructure.logging import get_logger

logger = get_logger("sysplatform.macos.clipboard")

class MacOSClipboardController(ClipboardController):
    async def read_clipboard(self) -> str:
        try:
            result = subprocess.run(["pbpaste"], capture_output=True, text=True, check=True)
            # Do not log clipboard contents
            logger.debug("Read clipboard")
            return result.stdout
        except Exception as e:
            logger.error("Failed to read clipboard", error=str(e))
            return ""

    async def write_clipboard(self, text: str) -> None:
        try:
            process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            process.communicate(input=text.encode('utf-8'))
            logger.debug("Wrote to clipboard")
        except Exception as e:
            logger.error("Failed to write to clipboard", error=str(e))

    async def clear_clipboard(self) -> None:
        await self.write_clipboard("")
