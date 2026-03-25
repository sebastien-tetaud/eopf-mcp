"""Session storage using JSON files."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

from models import Session, Message
from config_loader import get_config


class SessionStore:
    """Store chat sessions in JSON files."""

    def __init__(self):
        self.config = get_config()
        self.storage_dir = Path(self.config.session_storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def _get_session_path(self, session_id: str) -> Path:
        """Get path to session file."""
        return self.storage_dir / f"{session_id}.json"

    def create_session(self, title: str | None = None) -> Session:
        """Create a new chat session."""
        session_id = str(uuid.uuid4())
        now = datetime.now()

        session = Session(
            id=session_id,
            title=title or f"Chat {now.strftime('%Y-%m-%d %H:%M')}",
            created_at=now,
            updated_at=now,
            messages=[],
            metadata={}
        )

        self._save_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        path = self._get_session_path(session_id)

        if not path.exists():
            return None

        with open(path, 'r') as f:
            data = json.load(f)
            return Session(**data)

    def save_session(self, session: Session) -> None:
        """Save a session."""
        session.updated_at = datetime.now()
        self._save_session(session)

    def _save_session(self, session: Session) -> None:
        """Internal save method."""
        path = self._get_session_path(session.id)

        with open(path, 'w') as f:
            json.dump(session.model_dump(mode='json'), f, indent=2, default=str)

    def list_sessions(self, limit: int = 50) -> list[Session]:
        """List all sessions, sorted by updated_at descending."""
        sessions = []

        for path in self.storage_dir.glob("*.json"):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    sessions.append(Session(**data))
            except Exception as e:
                print(f"Error loading session {path}: {e}")

        # Sort by updated_at descending
        sessions.sort(key=lambda s: s.updated_at, reverse=True)

        return sessions[:limit]

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        path = self._get_session_path(session_id)

        if path.exists():
            path.unlink()
            return True

        return False

    def add_message(self, session_id: str, message: Message) -> Session:
        """Add a message to a session."""
        session = self.get_session(session_id)

        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.messages.append(message)
        self.save_session(session)

        return session
