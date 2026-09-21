import asyncio
import numpy as np
from typing import AsyncGenerator
import sounddevice as sd
import queue

from core.voice.interfaces import AudioSource
from infrastructure.logging import get_logger

logger = get_logger("infrastructure.audio.capture")

class LocalAudioSource(AudioSource):
    """
    Captures audio from the default local microphone.
    Emits chunks of audio as numpy arrays.
    """
    def __init__(self, sample_rate: int = 16000, channels: int = 1, chunk_size: int = 480):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self._queue: queue.Queue = queue.Queue()
        self._stream = None
        self._is_running = False

    def _audio_callback(self, indata, frames, time, status):
        if status:
            logger.warning("Audio capture status", status=str(status))
        # Flatten the array and put it in the queue
        self._queue.put(indata.copy().flatten())

    def start(self) -> None:
        if self._is_running:
            return
            
        self._is_running = True
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='int16',
            blocksize=self.chunk_size,
            callback=self._audio_callback
        )
        self._stream.start()
        logger.info("Local audio capture started", sample_rate=self.sample_rate)

    def stop(self) -> None:
        if not self._is_running:
            return
            
        self._is_running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        logger.info("Local audio capture stopped")

    async def get_audio_stream(self) -> AsyncGenerator[np.ndarray, None]:
        if not self._is_running:
            self.start()
            
        loop = asyncio.get_event_loop()
        while self._is_running:
            try:
                # Use executor to avoid blocking the event loop
                chunk = await loop.run_in_executor(None, self._queue.get, True, 0.1)
                yield chunk
            except queue.Empty:
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error("Error reading audio stream", error=str(e))
                break
