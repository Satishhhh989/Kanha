import sqlite3
import json
from typing import Any
from pathlib import Path
from pydantic import BaseModel, Field
from core.ai import Message, SystemMessage, UserMessage, AssistantMessage, ToolMessage
from infrastructure.logging import get_logger

logger = get_logger("core.agent.session")

class Session(BaseModel):
    session_id: str
    messages: list[Message] = Field(default_factory=list)

class SessionStore:
    """
    Manages persistent conversational sessions using SQLite.
    """
    def __init__(self, db_path: str = "kahna_sessions.db") -> None:
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    messages_json TEXT NOT NULL
                )
            """)
            
    def _serialize_messages(self, messages: list[Message]) -> str:
        return json.dumps([msg.model_dump() for msg in messages])
        
    def _deserialize_messages(self, data: str) -> list[Message]:
        raw = json.loads(data)
        messages = []
        for msg in raw:
            role = msg.get("role")
            if role == "system":
                messages.append(SystemMessage(**msg))
            elif role == "user":
                messages.append(UserMessage(**msg))
            elif role == "assistant":
                messages.append(AssistantMessage(**msg))
            elif role == "tool":
                messages.append(ToolMessage(**msg))
        return messages

    def get_session(self, session_id: str) -> Session:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT messages_json FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                messages = self._deserialize_messages(row[0])
                return Session(session_id=session_id, messages=messages)
            return Session(session_id=session_id)
            
    def save_session(self, session: Session) -> None:
        messages_json = self._serialize_messages(session.messages)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sessions (session_id, messages_json) VALUES (?, ?)",
                (session.session_id, messages_json)
            )

# Global session store
session_store = SessionStore()
