import numpy as np
from core.events.bus import EventBus
from core.events.models import BaseEvent, EventType
from infrastructure.logging import get_logger

logger = get_logger("infrastructure.audio.analyzer")

class AudioAnalyzer:
    """
    Analyzes audio chunks (e.g. from TTS playback) and emits metrics
    to drive the KAHNA visual orb.
    """
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        # Exponential moving average for smoothing
        self._smoothed_rms = 0.0
        self.smoothing_factor = 0.7

    def analyze_and_emit(self, audio_chunk: np.ndarray, session_id: str | None = None):
        """
        Analyzes a chunk of 16-bit PCM audio and emits a TTS_AUDIO_LEVEL event.
        """
        if len(audio_chunk) == 0:
            return
            
        # Convert to float for analysis
        audio_float = audio_chunk.astype(np.float32) / 32768.0
        
        # Calculate RMS (Root Mean Square)
        rms = np.sqrt(np.mean(np.square(audio_float)))
        
        # Smooth RMS
        self._smoothed_rms = (self.smoothing_factor * self._smoothed_rms) + ((1.0 - self.smoothing_factor) * rms)
        
        # Map to a 0.0 - 1.0 level (RMS rarely exceeds 0.3 for speech, so we scale it)
        scaled_level = min(1.0, self._smoothed_rms * 3.33)
        
        # For more complex visuals, we could do FFT here to get bass/mid/treble.
        # But RMS is sufficient for a fluid orb amplitude.
        
        event = BaseEvent(
            event_type=EventType.TTS_AUDIO_LEVEL,
            session_id=session_id,
            payload={
                "level": float(scaled_level),
                "rms": float(rms)
            }
        )
        self.event_bus.emit(event)
