#!/usr/bin/env python3
"""
Example Python client for the EOPF STAC Chat API.

This demonstrates how to use the FastAPI server programmatically.

Requirements:
    pip install requests sseclient-py

Usage:
    # Start the API server in one terminal:
    uv run python src/api_server.py

    # Run this script in another terminal:
    python examples/api_client_example.py
"""

import json
import requests
from sseclient import SSEClient

# API configuration
BASE_URL = "http://localhost:8000"


def create_session(title="Python Client Session"):
    """Create a new chat session."""
    response = requests.post(
        f"{BASE_URL}/api/sessions",
        json={"title": title}
    )
    response.raise_for_status()
    return response.json()


def send_message(session_id, message):
    """Send a message to a chat session."""
    response = requests.post(
        f"{BASE_URL}/api/chat/send",
        json={
            "session_id": session_id,
            "message": message
        }
    )
    response.raise_for_status()
    return response.json()


def stream_response(session_id):
    """Stream the chat response using Server-Sent Events."""
    messages = SSEClient(f"{BASE_URL}/api/chat/stream/{session_id}")

    full_text = ""

    for msg in messages:
        if msg.event == "":
            continue

        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            continue

        if msg.event == "message_start":
            print("\n🤖 Assistant is thinking...")

        elif msg.event == "tool_call":
            print(f"\n🔧 Calling tool: {data['name']}")
            print(f"   Input: {json.dumps(data['input'], indent=2)}")

        elif msg.event == "tool_result":
            print(f"\n✅ Tool result from {data['name']}")
            result_preview = data['result'][:200] + "..." if len(data['result']) > 200 else data['result']
            print(f"   {result_preview}")

        elif msg.event == "content_delta":
            text = data.get('text', '')
            print(text, end='', flush=True)
            full_text += text

        elif msg.event == "message_end":
            print(f"\n\n✓ Message complete (tools used: {', '.join(data.get('tools_used', []))})")
            break

        elif msg.event == "error":
            print(f"\n❌ Error: {data['message']}")
            break

    return full_text


def get_session(session_id):
    """Get session details and message history."""
    response = requests.get(f"{BASE_URL}/api/sessions/{session_id}")
    response.raise_for_status()
    return response.json()


def list_sessions():
    """List all chat sessions."""
    response = requests.get(f"{BASE_URL}/api/sessions")
    response.raise_for_status()
    return response.json()


def main():
    """Run example queries."""
    print("🚀 EOPF STAC Chat API Client Example\n")
    print("=" * 60)

    # Check if API is running
    try:
        response = requests.get(BASE_URL)
        response.raise_for_status()
        print(f"✓ Connected to API: {response.json()['message']}\n")
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to API at {BASE_URL}")
        print("   Make sure the API server is running:")
        print("   uv run python src/api_server.py\n")
        return

    # Create a session
    print("Creating new session...")
    session = create_session("Example Session - Earth Observation Data")
    session_id = session["id"]
    print(f"✓ Session created: {session_id}")
    print(f"  Title: {session['title']}\n")

    # Example 1: List collections
    print("=" * 60)
    print("Example 1: List all STAC collections")
    print("=" * 60)
    send_message(session_id, "List all available STAC collections")
    stream_response(session_id)

    # Example 2: Search for data
    print("\n" + "=" * 60)
    print("Example 2: Search for Sentinel-2 data over Paris")
    print("=" * 60)
    send_message(
        session_id,
        "Find Sentinel-2 L2A data over Paris (latitude 48.8566, longitude 2.3522) from January 2024"
    )
    stream_response(session_id)

    # Example 3: Get Zarr URLs
    print("\n" + "=" * 60)
    print("Example 3: Get Zarr URLs for the data")
    print("=" * 60)
    send_message(
        session_id,
        "Can you give me the Zarr URLs for the first result?"
    )
    stream_response(session_id)

    # Show session history
    print("\n" + "=" * 60)
    print("Session History")
    print("=" * 60)
    session = get_session(session_id)
    print(f"\nSession: {session['title']}")
    print(f"Messages: {len(session['messages'])}")
    print(f"Created: {session['created_at']}")
    print(f"Updated: {session['updated_at']}\n")

    for i, msg in enumerate(session['messages'], 1):
        print(f"\n{i}. [{msg['role'].upper()}] ({msg['timestamp']})")
        content_preview = msg['content'][:150] + "..." if len(msg['content']) > 150 else msg['content']
        print(f"   {content_preview}")
        if msg.get('tool_calls'):
            print(f"   Tools used: {', '.join(msg['tool_calls'])}")

    # List all sessions
    print("\n" + "=" * 60)
    print("All Sessions")
    print("=" * 60)
    sessions = list_sessions()
    print(f"\nTotal sessions: {len(sessions)}\n")
    for session in sessions[:5]:  # Show first 5
        print(f"- {session['title']} ({session['id'][:8]}...)")
        print(f"  Created: {session['created_at']}, Messages: {len(session['messages'])}")

    print("\n" + "=" * 60)
    print("✓ Example complete!")
    print("=" * 60)
    print(f"\nYou can view the full session at:")
    print(f"http://localhost:8000/api/sessions/{session_id}")


if __name__ == "__main__":
    main()
