import asyncio
from enum import Enum
from typing import Optional
import numpy as np

from core.events.bus import EventBus
from core.events.models import BaseEvent, EventType
from core.voice.interfaces import (
    AudioSource, WakeWordDetector, VoiceActivityDetector, 
    SpeechRecognizer, TextToSpeech
)
from infrastructure.audio.analyzer import AudioAnalyzer
from infrastructure.logging import get_logger

logger = get_logger("core.voice.session")

class VoiceState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    TRANSCRIBING = "TRANSCRIBING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"

class VoiceSessionManager:
    """
    Manages the lifecycle of a voice session:
    IDLE -> WAKE_DETECTED -> LISTENING -> TRANSCRIBING -> PROCESSING -> SPEAKING -> IDLE
    """
    def __init__(
        self,
        event_bus: EventBus,
        audio_source: AudioSource,
        vad: VoiceActivityDetector,
        wake_word: WakeWordDetector,
        stt: SpeechRecognizer,
        tts: TextToSpeech,
        audio_analyzer: AudioAnalyzer,
        agent_callback
    ):
        self.event_bus = event_bus
        self.audio_source = audio_source
        self.vad = vad
        self.wake_word = wake_word
        self.stt = stt
        self.tts = tts
        self.audio_analyzer = audio_analyzer
        self.agent_callback = agent_callback
        
        self.state = VoiceState.IDLE
        self._is_running = False
        self._interrupted = False
        self.session_id: Optional[str] = None
        
    def _change_state(self, new_state: VoiceState, session_id: Optional[str] = None):
        if self.state != new_state:
            logger.info("Voice state changed", old_state=self.state, new_state=new_state)
            self.state = new_state
            self.event_bus.emit(BaseEvent(
                event_type=EventType.AGENT_STATE_CHANGED,
                session_id=session_id or self.session_id,
                payload={"state": new_state}
            ))

    async def start(self):
        if self._is_running:
            return
            
        self._is_running = True
        self.audio_source.start()
        
        try:
            # We use an async generator to consume audio
            stream = self.audio_source.get_audio_stream()
            
            audio_buffer = []
            listening_silence_count = 0
            barge_in_count = 0
            idle_speech_count = 0
            MAX_SILENCE_CHUNKS = 35 # ~1.05s of silence after speech to start processing
            
            async for chunk in stream:
                if not self._is_running:
                    break
                    
                is_speech = self.vad.is_speech(chunk)
                rms = float(np.sqrt(np.mean(np.square(chunk.astype(np.float32) / 32768.0))))
                
                if self.state == VoiceState.IDLE:
                    # Require clear human voice level (rms > 0.030) so minor clicks/breath don't trigger wake
                    if is_speech and rms > 0.030:
                        idle_speech_count += 1
                        if idle_speech_count >= 2: # ~60ms of verified voice
                            import uuid
                            self.session_id = str(uuid.uuid4())
                            self._interrupted = False
                            self._change_state(VoiceState.LISTENING)
                            audio_buffer = [chunk]
                            listening_silence_count = 0
                            barge_in_count = 0
                            idle_speech_count = 0
                    else:
                        idle_speech_count = max(0, idle_speech_count - 1)
                        
                elif self.state == VoiceState.LISTENING:
                    audio_buffer.append(chunk)
                    
                    if is_speech:
                        listening_silence_count = 0
                        # Emit voice activity for UI
                        self.event_bus.emit(BaseEvent(
                            event_type=EventType.VOICE_ACTIVITY,
                            session_id=self.session_id,
                            payload={"active": True}
                        ))
                    else:
                        listening_silence_count += 1
                        
                    # Stop listening if we've accumulated enough silence after speech
                    if listening_silence_count > MAX_SILENCE_CHUNKS and len(audio_buffer) > 20:
                        current_session_id = self.session_id
                        self._change_state(VoiceState.TRANSCRIBING)
                        asyncio.create_task(self._process_utterance(np.concatenate(audio_buffer), current_session_id))
                        audio_buffer = []
                        listening_silence_count = 0
                        
                elif self.state == VoiceState.SPEAKING:
                    # User talks while KAHNA is speaking (Barge-in / Interruption)
                    # Requires loud, clear user voice (rms >= 0.075) for 4 chunks (~120ms) so small noises/speaker bleed never trigger cutoff
                    if is_speech and rms >= 0.075:
                        barge_in_count += 1
                        if barge_in_count >= 4: # ~120ms of sustained loud user speech
                            logger.info("Loud voice barge-in detected during SPEAKING: cutting off speech", rms=rms)
                            self.interrupt()
                            import uuid
                            self.session_id = str(uuid.uuid4())
                            self._interrupted = False
                            self._change_state(VoiceState.LISTENING)
                            audio_buffer = [chunk]
                            listening_silence_count = 0
                            barge_in_count = 0
                    else:
                        barge_in_count = max(0, barge_in_count - 1)

                elif self.state in (VoiceState.PROCESSING, VoiceState.TRANSCRIBING):
                    # User talks while KAHNA is processing (requires rms >= 0.050 for 3 chunks)
                    if is_speech and rms >= 0.050:
                        barge_in_count += 1
                        if barge_in_count >= 3:
                            logger.info("Voice interruption detected during PROCESSING: cancelling to listen", rms=rms)
                            self.interrupt()
                            import uuid
                            self.session_id = str(uuid.uuid4())
                            self._interrupted = False
                            self._change_state(VoiceState.LISTENING)
                            audio_buffer = [chunk]
                            listening_silence_count = 0
                            barge_in_count = 0
                    else:
                        barge_in_count = max(0, barge_in_count - 1)
                        
        except Exception as e:
            logger.error("Voice loop error", error=str(e))
            self.stop()
            
    def stop(self):
        self._is_running = False
        self.audio_source.stop()
        self._change_state(VoiceState.IDLE)
        
    def interrupt(self):
        """Interrupts current processing or speech."""
        self._interrupted = True
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass
        if self.state in [VoiceState.SPEAKING, VoiceState.PROCESSING]:
            self._change_state(VoiceState.IDLE)

    async def _process_utterance(self, audio_data: np.ndarray, session_id: str):
        try:
            # 1. STT
            transcript = await self.stt.transcribe(audio_data)
            if self._interrupted or self.session_id != session_id:
                return

            self.event_bus.emit(BaseEvent(
                event_type=EventType.TRANSCRIPT_FINAL,
                session_id=session_id,
                payload={"text": transcript}
            ))
            
            if not transcript or not transcript.strip():
                if self.session_id == session_id:
                    self._change_state(VoiceState.IDLE)
                return
                
            # Interruption check
            if "stop" in transcript.lower().strip() and len(transcript) < 15:
                self.interrupt()
                return

            # 2. Agent Processing
            self._change_state(VoiceState.PROCESSING, session_id)
            response_text = await self.agent_callback(session_id, transcript)
            
            if self._interrupted or self.session_id != session_id:
                return

            # 3. TTS & Real Playback
            self._change_state(VoiceState.SPEAKING, session_id)
            
            # Emit live caption to UI
            self.event_bus.emit(BaseEvent(
                event_type=EventType.TTS_TEXT,
                session_id=session_id,
                payload={"text": response_text}
            ))
            
            self.event_bus.emit(BaseEvent(
                event_type=EventType.TTS_STARTED,
                session_id=session_id,
                payload={}
            ))
            
            # Synthesize full audio
            full_audio = await self.tts.synthesize(response_text)
            
            if len(full_audio) > 0 and not self._interrupted and self.session_id == session_id:
                import sounddevice as sd
                # Start physical speaker playback
                sd.play(full_audio, 16000)
                
                # Stream chunks in real-time to animate the 3D Orb
                chunk_size = 480 # 30ms @ 16kHz
                for i in range(0, len(full_audio), chunk_size):
                    if self._interrupted or self.session_id != session_id:
                        sd.stop()
                        break
                    chunk = full_audio[i:i + chunk_size]
                    self.audio_analyzer.analyze_and_emit(chunk, session_id)
                    await asyncio.sleep(len(chunk) / 16000.0)
                
                if not self._interrupted and self.session_id == session_id:
                    await asyncio.sleep(0.05)
                    
            if self.session_id == session_id and not self._interrupted:
                self.event_bus.emit(BaseEvent(
                    event_type=EventType.TTS_ENDED,
                    session_id=session_id,
                    payload={}
                ))
            
        except Exception as e:
            logger.error("Error processing utterance", error=str(e), exc_info=True)
            self.event_bus.emit(BaseEvent(
                event_type=EventType.AGENT_ERROR,
                session_id=session_id,
                payload={"error": str(e)}
            ))
        finally:
            if not self._interrupted and self.session_id == session_id:
                self._change_state(VoiceState.IDLE, session_id)
