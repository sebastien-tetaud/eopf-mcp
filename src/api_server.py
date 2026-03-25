"""FastAPI server for React frontend."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

from chat_handler import get_chat_handler
from session_store import SessionStore
from models import (
    SendMessageRequest,
    SendMessageResponse,
    CreateSessionRequest,
    Session,
    Message,
    StreamEvent,
)
from config_loader import get_config


# Initialize session store
session_store = SessionStore()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize chat handler on startup."""
    print("🚀 Initializing API server...")

    # Initialize chat handler (MCP connection)
    await get_chat_handler()

    print("✓ API server ready")
    yield
    print("👋 Shutting down API server...")


# Create FastAPI app
app = FastAPI(
    title="EOPF STAC Chat API",
    description="API for React frontend to interact with MCP server",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
config = get_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "EOPF STAC Chat API",
        "version": "1.0.0"
    }


@app.get("/api/sessions", response_model=list[Session])
async def list_sessions(limit: int = 50):
    """List all chat sessions."""
    sessions = session_store.list_sessions(limit=limit)
    return sessions


@app.post("/api/sessions", response_model=Session)
async def create_session(request: CreateSessionRequest):
    """Create a new chat session."""
    session = session_store.create_session(title=request.title)
    return session


@app.get("/api/sessions/{session_id}", response_model=Session)
async def get_session(session_id: str):
    """Get a specific session."""
    session = session_store.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    deleted = session_store.delete_session(session_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"status": "deleted", "session_id": session_id}


@app.post("/api/chat/send", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest):
    """Send a message to a chat session."""
    # Verify session exists
    session = session_store.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Add user message
    user_message = Message(
        role="user",
        content=request.message,
        timestamp=datetime.now()
    )
    session_store.add_message(request.session_id, user_message)

    # Start processing in background (client will connect to stream endpoint)
    message_id = f"msg_{datetime.now().timestamp()}"

    return SendMessageResponse(
        session_id=request.session_id,
        message_id=message_id,
        status="processing"
    )


@app.get("/api/chat/stream/{session_id}")
async def stream_response(session_id: str):
    """
    Stream chat response using Server-Sent Events (SSE).

    This endpoint returns a stream of events as the LLM processes the message.
    """
    # Get session
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get the last user message
    if not session.messages or session.messages[-1].role != "user":
        raise HTTPException(status_code=400, detail="No user message to process")

    user_message = session.messages[-1].content
    history = session.messages[:-1]  # All messages except the last one

    # Get chat handler
    chat_handler = await get_chat_handler()

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events."""
        try:
            full_response = ""
            tool_calls = []
            tool_calls_by_name = {}

            async for event in chat_handler.process_message(user_message, history):
                # Send SSE event
                yield f"event: {event.event}\n"
                yield f"data: {event.model_dump_json()}\n\n"

                # Accumulate response
                if event.event == "content_delta":
                    full_response += event.data.get("text", "")
                elif event.event == "tool_call":
                    # Store tool call for later merging with result
                    tool_name = event.data.get("name")
                    tool_calls_by_name[tool_name] = {
                        "name": tool_name,
                        "input": event.data.get("input"),
                        "result": None  # Will be filled in by tool_result event
                    }
                elif event.event == "tool_result":
                    # Merge result with tool call
                    tool_name = event.data.get("name")
                    if tool_name in tool_calls_by_name:
                        tool_calls_by_name[tool_name]["result"] = event.data.get("result")
                        # Add completed tool call to list
                        tool_calls.append(tool_calls_by_name[tool_name])
                elif event.event == "message_end":
                    # Save assistant message
                    assistant_message = Message(
                        role="assistant",
                        content=full_response,
                        timestamp=datetime.now(),
                        tool_calls=tool_calls if tool_calls else None
                    )
                    session_store.add_message(session_id, assistant_message)

        except Exception as e:
            # Send error event
            error_event = StreamEvent(event="error", data={"message": str(e)})
            yield f"event: error\n"
            yield f"data: {error_event.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        },
    )


def main():
    """Run the API server."""
    config = get_config()

    print(f"🚀 Starting EOPF STAC Chat API on {config.api_host}:{config.api_port}")
    print(f"📡 CORS origins: {config.api_cors_origins}")

    uvicorn.run(
        app,
        host=config.api_host,
        port=config.api_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
