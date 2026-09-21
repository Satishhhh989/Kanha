import asyncio
import os
import tempfile
import wave
import subprocess
import numpy as np
from typing import AsyncGenerator
from core.voice.interfaces import TextToSpeech
from infrastructure.logging import get_logger

logger = get_logger("infrastructure.audio.tts")

class PiperTTS(TextToSpeech):
    """
    Text-to-Speech using Piper with native macOS speech synthesis fallback.
    Outputs 16kHz 16-bit Mono PCM audio.
    """
    def __init__(self, model_path: str = "en_US-lessac-medium.onnx"):
        self.model_path = model_path
        self.voice = None
        try:
            from piper import PiperVoice
            if os.path.exists(model_path):
                self.voice = PiperVoice.load(model_path)
                logger.info("Piper TTS loaded", model_path=model_path)
        except ImportError:
            pass

        if self.voice is None:
            logger.info("Using native system TTS fallback")

    def _synthesize_system(self, text: str) -> np.ndarray:
        """Synthesizes speech to 16kHz int16 PCM using OS native speech (macOS say or Windows PowerShell SAPI)."""
        import sys
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            clean_text = text.replace('"', '').replace("'", "").strip()
            if not clean_text:
                return np.zeros(0, dtype=np.int16)

            if sys.platform == "darwin":
                cmd = ["/usr/bin/say", "-v", "Samantha", "-o", tmp_path, "--data-format=LEI16@16000", clean_text]
                subprocess.run(cmd, check=True, capture_output=True)
            elif sys.platform == "win32":
                ps_script = f"""
                Add-Type -AssemblyName System.Speech;
                $s = New-Object System.Speech.Synthesis.SpeechSynthesizer;
                $s.SetOutputToWaveFile('{tmp_path}');
                $s.Speak('{clean_text}');
                $s.Dispose();
                """
                subprocess.run(["powershell", "-Command", ps_script], check=True, capture_output=True)
            else:
                return np.zeros(0, dtype=np.int16)

            with wave.open(tmp_path, "rb") as w:
                n_frames = w.getnframes()
                raw = w.readframes(n_frames)
                framerate = w.getframerate()
                audio_data = np.frombuffer(raw, dtype=np.int16)
                if framerate != 16000 and len(audio_data) > 0:
                    import scipy.signal
                    target_len = int(len(audio_data) * 16000 / framerate)
                    audio_data = scipy.signal.resample(audio_data, target_len).astype(np.int16)
                return audio_data
        except Exception as e:
            logger.error("System TTS synthesis failed", error=str(e))
            return np.zeros(0, dtype=np.int16)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    async def synthesize(self, text: str) -> np.ndarray:
        """
        Synthesizes text into a numpy array (16kHz, int16).
        """
        if not text or not text.strip():
            return np.zeros(0, dtype=np.int16)
            
        loop = asyncio.get_event_loop()

        if self.voice is not None:
            def _synthesize_piper():
                audio_stream = self.voice.synthesize_stream_raw(text)
                chunks = list(audio_stream)
                if chunks:
                    return np.concatenate([np.frombuffer(c, dtype=np.int16) for c in chunks])
                return np.zeros(0, dtype=np.int16)
            try:
                return await loop.run_in_executor(None, _synthesize_piper)
            except Exception as e:
                logger.error("Piper synthesis failed, falling back to system TTS", error=str(e))

        return await loop.run_in_executor(None, self._synthesize_system, text)

    async def synthesize_stream(self, text: str) -> AsyncGenerator[np.ndarray, None]:
        """
        Synthesizes text and yields chunks of 16kHz audio (480 samples / 30ms).
        """
        audio_data = await self.synthesize(text)
        if len(audio_data) == 0:
            return

        chunk_size = 480 # 30ms frame
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i:i + chunk_size]
