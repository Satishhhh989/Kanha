import numpy as np
from core.voice.interfaces import SpeechRecognizer
from infrastructure.logging import get_logger

logger = get_logger("infrastructure.audio.stt")

class WhisperRecognizer(SpeechRecognizer):
    """
    Speech-to-Text using faster-whisper.
    """
    def __init__(self, model_size: str = "base.en", device: str = "cpu"):
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(model_size, device=device, compute_type="int8")
            logger.info("Whisper model loaded", model_size=model_size, device=device)
        except ImportError:
            logger.error("faster-whisper is not installed. STT will not work.")
            self.model = None

    async def transcribe(self, audio_data: np.ndarray) -> str:
        """
        Transcribes the provided audio data to text.
        audio_data is expected to be a 1D numpy array of float32, normalized between -1.0 and 1.0, 16kHz.
        """
        if self.model is None:
            return ""
            
        try:
            import asyncio
            
            # Convert int16 to float32 if needed
            if audio_data.dtype == np.int16:
                audio_float = audio_data.astype(np.float32) / 32768.0
            else:
                audio_float = audio_data

            loop = asyncio.get_event_loop()
            
            def _transcribe():
                segments, info = self.model.transcribe(audio_float, beam_size=5)
                return " ".join([segment.text for segment in segments]).strip()
                
            text = await loop.run_in_executor(None, _transcribe)
            logger.debug("Transcribed text", text=text)
            return text
            
        except Exception as e:
            logger.error("Transcription failed", error=str(e))
            return ""
