from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import time
import uuid

class Point(BaseModel):
    x: int
    y: int

class ScreenFrame(BaseModel):
    image_data: bytes = Field(exclude=True) # Excluded from logs automatically
    width: int
    height: int
    display_id: str
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ActionType(str, Enum):
    OPEN_APPLICATION = "OPEN_APPLICATION"
    CLOSE_APPLICATION = "CLOSE_APPLICATION"
    FOCUS_WINDOW = "FOCUS_WINDOW"
    MOUSE_MOVE = "MOUSE_MOVE"
    MOUSE_CLICK = "MOUSE_CLICK"
    MOUSE_DOUBLE_CLICK = "MOUSE_DOUBLE_CLICK"
    MOUSE_SCROLL = "MOUSE_SCROLL"
    MOUSE_DRAG = "MOUSE_DRAG"
    KEY_PRESS = "KEY_PRESS"
    KEY_TYPE = "KEY_TYPE"
    KEY_HOTKEY = "KEY_HOTKEY"
    CLIPBOARD_READ = "CLIPBOARD_READ"
    CLIPBOARD_WRITE = "CLIPBOARD_WRITE"
    SCREEN_CAPTURE = "SCREEN_CAPTURE"
    BROWSER_NAVIGATE = "BROWSER_NAVIGATE"
    BROWSER_CLICK = "BROWSER_CLICK"
    BROWSER_TYPE = "BROWSER_TYPE"

class ComputerAction(BaseModel):
    action_type: ActionType
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timeout: float = 10.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TaskState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class UIElement(BaseModel):
    """Stub for future vision subsystem."""
    element_type: str
    bounding_box: Dict[str, int] # x, y, width, height
    text: Optional[str] = None
    confidence: float
    state: str
    interaction_capabilities: List[str] = Field(default_factory=list)

class ComputerState(BaseModel):
    active_application: Optional[str] = None
    active_window: Optional[str] = None
    screen_dimensions: Optional[Dict[str, int]] = None
    mouse_position: Optional[Point] = None
    clipboard_state: Optional[str] = None # Or truncated
    running_applications: List[str] = Field(default_factory=list)
    available_displays: List[str] = Field(default_factory=list)
