# API Examples

This directory contains example code showing how to use the FastAPI server programmatically.

## Available Examples

### 1. Bash/Curl Example (`api_curl_example.sh`)

Simple shell script using curl to interact with the API.

**Requirements**: `curl`, `jq`

**Usage**:
```bash
# Start the API server
uv run python src/api_server.py

# Run the example
./examples/api_curl_example.sh
```

### 2. Python Client Example (`api_client_example.py`)

Complete Python example showing how to:
- Create sessions
- Send messages
- Stream responses with Server-Sent Events
- View session history

**Requirements**:
```bash
pip install requests sseclient-py
```

**Usage**:
```bash
# Start the API server
uv run python src/api_server.py

# Run the example
python examples/api_client_example.py
```

## More Examples

For additional examples in other languages, see:

- **JavaScript/TypeScript**: [docs/API_USAGE.md](../docs/API_USAGE.md#javascripttypescript-client-example)
- **iOS (Swift)**: [docs/API_USAGE.md](../docs/API_USAGE.md#ios-swift)
- **Android (Kotlin)**: [docs/API_USAGE.md](../docs/API_USAGE.md#android-kotlin)

## API Documentation

- **Full API Guide**: [docs/API_USAGE.md](../docs/API_USAGE.md)
- **OpenAPI/Swagger**: http://localhost:8000/docs (when server is running)
- **ReDoc**: http://localhost:8000/redoc (when server is running)

## Quick Reference

### API Endpoints

```
GET  /                          - Health check
GET  /api/sessions              - List all sessions
POST /api/sessions              - Create new session
GET  /api/sessions/{id}         - Get session details
DELETE /api/sessions/{id}       - Delete session
POST /api/chat/send             - Send message
GET  /api/chat/stream/{id}      - Stream response (SSE)
```

### Minimal Example

```bash
# Create session
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "Test"}'

# Send message (replace SESSION_ID)
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{"session_id": "SESSION_ID", "message": "List collections"}'

# Stream response
curl -N http://localhost:8000/api/chat/stream/SESSION_ID
```
