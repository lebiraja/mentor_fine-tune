"""Session management service."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from backend.core.exceptions import SessionError


class Session:
    """Represents a conversation session."""

    def __init__(self, session_id: str):
        """Initialize a session.

        Args:
            session_id: Unique session identifier
        """
        self.id = session_id
        self.created_at = datetime.now()
        self.history: List[Dict[str, Any]] = []
        self.emotion_history: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "history": self.history,
            "emotion_history": self.emotion_history,
        }


class SessionService:
    """Service for managing conversation sessions."""

    def __init__(self):
        """Initialize session service."""
        self.sessions: Dict[str, Session] = {}

    def create_session(self) -> str:
        """Create a new conversation session.

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = Session(session_id)
        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session object or None
        """
        return self.sessions.get(session_id)

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of conversation turns

        Raises:
            SessionError: If session not found
        """
        session = self.get_session(session_id)
        if session is None:
            raise SessionError(f"Session '{session_id}' not found")

        return session.history

    def add_turn(
        self,
        session_id: str,
        user_text: str,
        emotion: Dict[str, Any],
        response: str,
    ) -> None:
        """Add a conversation turn to session history.

        Args:
            session_id: Session identifier
            user_text: User's input text
            emotion: Detected emotion
            response: Assistant's response

        Raises:
            SessionError: If session not found
        """
        session = self.get_session(session_id)
        if session is None:
            raise SessionError(f"Session '{session_id}' not found")

        # Add user turn
        session.history.append({
            "role": "user",
            "content": user_text,
            "emotion": emotion,
            "timestamp": datetime.now().isoformat(),
        })

        # Add assistant turn
        session.history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat(),
        })

        # Track emotion history
        session.emotion_history.append({
            "timestamp": datetime.now().isoformat(),
            "emotion": emotion,
        })

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all sessions as dictionaries.

        Returns:
            Dict of session_id -> session_dict
        """
        return {sid: session.to_dict() for sid, session in self.sessions.items()}

    def export_session(self, session_id: str) -> Dict[str, Any]:
        """Export a session as a dictionary.

        Args:
            session_id: Session identifier

        Returns:
            Session data

        Raises:
            SessionError: If session not found
        """
        session = self.get_session(session_id)
        if session is None:
            raise SessionError(f"Session '{session_id}' not found")

        return session.to_dict()
