"""Pydantic models for API requests/responses."""

from typing import Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Chat message model."""
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    tool_calls: list[dict[str, Any]] | None = None


class SendMessageRequest(BaseModel):
    """Request to send a message."""
    session_id: str
    message: str


class SendMessageResponse(BaseModel):
    """Response after sending a message."""
    session_id: str
    message_id: str
    status: Literal["queued", "processing", "completed", "error"]


class Session(BaseModel):
    """Chat session model."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[Message]
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreateSessionRequest(BaseModel):
    """Request to create a new session."""
    title: str | None = None


class StreamEvent(BaseModel):
    """SSE stream event."""
    event: Literal["message_start", "content_delta", "tool_call", "tool_result", "message_end", "error"]
    data: dict[str, Any]
