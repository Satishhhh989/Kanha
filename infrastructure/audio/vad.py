import webrtcvad
import numpy as np
from core.voice.interfaces import VoiceActivityDetector
from infrastructure.logging import get_logger

logger = get_logger("infrastructure.audio.vad")

class WebRTCVAD(VoiceActivityDetector):
    """
    Voice Activity Detection using WebRTC.
    Expects 16-bit PCM audio, typically 16000Hz.
    """
    def __init__(self, sample_rate: int = 16000, aggressiveness: int = 2):
        self.sample_rate = sample_rate
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(aggressiveness)
        # WebRTCVAD requires chunks of 10, 20, or 30ms
        self.frame_duration_ms = 30
        self.frame_size = int(sample_rate * self.frame_duration_ms / 1000)

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """
        Detects if the provided audio chunk contains speech.
        The chunk must be exactly the frame size.
        """
        if len(audio_chunk) != self.frame_size:
            logger.warning("VAD received incorrect chunk size", expected=self.frame_size, received=len(audio_chunk))
            return False
            
        # Ensure audio is bytes representation of int16
        audio_bytes = audio_chunk.astype(np.int16).tobytes()
        try:
            return self.vad.is_speech(audio_bytes, self.sample_rate)
        except Exception as e:
            logger.error("VAD error", error=str(e))
            return False
