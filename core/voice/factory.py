from core.events.bus import event_bus
from core.agent import agent_runtime
from core.voice.session import VoiceSessionManager
from infrastructure.audio.capture import LocalAudioSource
from infrastructure.audio.vad import WebRTCVAD
from infrastructure.audio.wake_word import OpenWakeWordDetector
from infrastructure.audio.stt import WhisperRecognizer
from infrastructure.audio.tts import PiperTTS
from infrastructure.audio.analyzer import AudioAnalyzer

# Create singletons for the voice pipeline
audio_source = LocalAudioSource()
vad = WebRTCVAD()
wake_word = OpenWakeWordDetector()
stt = WhisperRecognizer()
tts = PiperTTS()
audio_analyzer = AudioAnalyzer(event_bus=event_bus)

voice_manager = VoiceSessionManager(
    event_bus=event_bus,
    audio_source=audio_source,
    vad=vad,
    wake_word=wake_word,
    stt=stt,
    tts=tts,
    audio_analyzer=audio_analyzer,
    agent_callback=agent_runtime.chat
)
