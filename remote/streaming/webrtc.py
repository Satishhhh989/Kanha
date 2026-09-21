import asyncio
from aiortc import VideoStreamTrack, RTCPeerConnection, RTCSessionDescription
from av import VideoFrame
import fractions
import time
from infrastructure.logging import get_logger

logger = get_logger("core.remote.streaming")

class ScreenVideoStreamTrack(VideoStreamTrack):
    """
    A video track that returns screen frames from KAHNA's ScreenCaptureService.
    """
    def __init__(self):
        super().__init__()  # don't forget this!
        from core.computer.screen import screen_service
        self.screen_service = screen_service
        # Optional: Keep track of timing to enforce FPS limit
        self.last_frame_time = 0
        self.target_fps = 10
        self.frame_duration = 1.0 / self.target_fps
        self._running = True
        
    def stop_capture(self):
        self._running = False

    async def recv(self) -> VideoFrame:
        """
        Called by aiortc when a new frame is needed.
        """
        if not self._running:
            # Depending on aiortc, raising an exception or returning None might be needed to stop
            raise Exception("Stream stopped")

        pts, time_base = await self.next_timestamp()
        
        # Rate limit
        now = time.time()
        elapsed = now - self.last_frame_time
        if elapsed < self.frame_duration:
            await asyncio.sleep(self.frame_duration - elapsed)
            
        # Capture from MSS
        img = self.screen_service.capture()
        if not img:
            # Fallback black frame if capture fails
            import numpy as np
            img_array = np.zeros((480, 640, 3), dtype=np.uint8)
        else:
            import numpy as np
            # MSS returns BGRA. Convert to BGR/RGB for av VideoFrame
            img_array = np.array(img.convert("RGB"))
            
        self.last_frame_time = time.time()
        
        # Create aiortc frame
        frame = VideoFrame.from_ndarray(img_array, format="rgb24")
        frame.pts = pts
        frame.time_base = time_base
        
        return frame

class StreamSession:
    """Manages an active WebRTC session for a remote client."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.pc = RTCPeerConnection()
        self.track = ScreenVideoStreamTrack()
        self.pc.addTrack(self.track)
        
    async def stop(self):
        self.track.stop_capture()
        await self.pc.close()
        
class StreamSessionManager:
    """Manages multiple active screen streaming sessions."""
    def __init__(self):
        self.sessions = {}
        
    def create_session(self, session_id: str) -> StreamSession:
        session = StreamSession(session_id)
        self.sessions[session_id] = session
        return session
        
    async def end_session(self, session_id: str):
        if session_id in self.sessions:
            await self.sessions[session_id].stop()
            del self.sessions[session_id]

stream_manager = StreamSessionManager()
