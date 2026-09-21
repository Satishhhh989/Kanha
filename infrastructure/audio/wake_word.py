import numpy as np
from core.voice.interfaces import WakeWordDetector
from infrastructure.logging import get_logger

logger = get_logger("infrastructure.audio.wake_word")

class OpenWakeWordDetector(WakeWordDetector):
    """
    Bypass wake word detection to avoid tflite/onnx crashes.
    Instead, it triggers automatically after a brief delay so you can just talk.
    """
    def __init__(self, model_paths: list[str] = None):
        self.triggered = False

    def detect(self, audio_chunk: np.ndarray) -> bool:
        if not self.triggered:
            self.triggered = True
            return True
        return False

    def detect(self, audio_chunk: np.ndarray) -> bool:
        """
        Feeds an audio chunk to the model and returns True if the wake word is detected.
        OpenWakeWord expects 16-bit 16kHz PCM audio.
        """
        if self.model is None:
            return False
            
        try:
            prediction = self.model.predict(audio_chunk)
            # prediction is a dict: {"model_name": score}
            for model_name, score in prediction.items():
                if score > 0.5: # Threshold can be made configurable
                    logger.debug("Wake word detected", model=model_name, score=score)
                    return True
        except Exception as e:
            logger.error("Error during wake word detection", error=str(e))
            
        return False
