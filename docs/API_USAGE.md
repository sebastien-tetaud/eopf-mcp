# FastAPI Standalone Usage Guide

The FastAPI server in `src/api_server.py` is a **fully standalone REST API** that can be used independently without any frontend. This guide shows how to use it.

## Quick Start

### 1. Start the API Server

```bash
uv run python src/api_server.py
```

The API will be available at `http://localhost:8000`.

### 2. View API Documentation

Open your browser and visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check

```bash
curl http://localhost:8000/
```

Response:
```json
{
  "status": "ok",
  "message": "EOPF STAC Chat API",
  "version": "1.0.0"
}
```

### Session Management

#### Create a Session

```bash
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "My Earth Observation Chat"}'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "My Earth Observation Chat",
  "created_at": "2024-03-20T10:30:00",
  "updated_at": "2024-03-20T10:30:00",
  "messages": [],
  "metadata": {}
}
```

#### List All Sessions

```bash
curl http://localhost:8000/api/sessions
```

#### Get a Specific Session

```bash
curl http://localhost:8000/api/sessions/{session_id}
```

#### Delete a Session

```bash
curl -X DELETE http://localhost:8000/api/sessions/{session_id}
```

### Chat Operations

#### Send a Message

```bash
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "List all available STAC collections"
  }'
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_id": "msg_1234567890",
  "status": "processing"
}
```

#### Stream the Response (Server-Sent Events)

```bash
curl -N http://localhost:8000/api/chat/stream/{session_id}
```

The response will be streamed as Server-Sent Events:

```
event: message_start
data: {"timestamp": "2024-03-20T10:30:01"}

event: tool_call
data: {"name": "list_collections", "input": {}}

event: tool_result
data: {"name": "list_collections", "result": "[...]"}

event: content_delta
data: {"text": "Here are the available STAC collections:\n\n"}

event: content_delta
data: {"text": "1. SENTINEL-2-L1C\n2. SENTINEL-2-L2A\n..."}

event: message_end
data: {"timestamp": "2024-03-20T10:30:05", "tools_used": ["list_collections"]}
```

## Python Client Example

```python
import requests
import json
from sseclient import SSEClient  # pip install sseclient-py

# API base URL
BASE_URL = "http://localhost:8000"

# 1. Create a session
response = requests.post(
    f"{BASE_URL}/api/sessions",
    json={"title": "Python Client Session"}
)
session = response.json()
session_id = session["id"]
print(f"Created session: {session_id}")

# 2. Send a message
response = requests.post(
    f"{BASE_URL}/api/chat/send",
    json={
        "session_id": session_id,
        "message": "Find Sentinel-2 data over Paris from January 2024"
    }
)
print("Message sent, streaming response...")

# 3. Stream the response
messages = SSEClient(f"{BASE_URL}/api/chat/stream/{session_id}")
for msg in messages:
    if msg.event != "":
        data = json.loads(msg.data)
        print(f"[{msg.event}] {data}")

# 4. Get session history
response = requests.get(f"{BASE_URL}/api/sessions/{session_id}")
session = response.json()
print(f"\nConversation history ({len(session['messages'])} messages):")
for msg in session["messages"]:
    print(f"{msg['role']}: {msg['content'][:100]}...")
```

## JavaScript/TypeScript Client Example

```typescript
// Create a session
const createSession = async () => {
  const response = await fetch('http://localhost:8000/api/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: 'JS Client Session' })
  });
  return await response.json();
};

// Send a message
const sendMessage = async (sessionId: string, message: string) => {
  await fetch('http://localhost:8000/api/chat/send', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message })
  });
};

// Stream response with EventSource
const streamResponse = (sessionId: string) => {
  const eventSource = new EventSource(
    `http://localhost:8000/api/chat/stream/${sessionId}`
  );

  eventSource.addEventListener('message_start', (e) => {
    console.log('Message started:', JSON.parse(e.data));
  });

  eventSource.addEventListener('content_delta', (e) => {
    const data = JSON.parse(e.data);
    console.log('Text:', data.text);
  });

  eventSource.addEventListener('tool_call', (e) => {
    const data = JSON.parse(e.data);
    console.log('Tool called:', data.name);
  });

  eventSource.addEventListener('message_end', (e) => {
    console.log('Message complete:', JSON.parse(e.data));
    eventSource.close();
  });

  eventSource.addEventListener('error', (e) => {
    console.error('Error:', JSON.parse(e.data));
    eventSource.close();
  });
};

// Usage
(async () => {
  const session = await createSession();
  await sendMessage(session.id, 'List all STAC collections');
  streamResponse(session.id);
})();
```

## Using with Mobile Apps

The REST API can be used directly from mobile applications:

### iOS (Swift)

```swift
import Foundation

struct Session: Codable {
    let id: String
    let title: String
    let created_at: String
    let updated_at: String
    let messages: [Message]
}

struct Message: Codable {
    let role: String
    let content: String
    let timestamp: String
}

class EOPFAPIClient {
    let baseURL = "http://localhost:8000"

    func createSession() async throws -> Session {
        let url = URL(string: "\(baseURL)/api/sessions")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(["title": "iOS App Session"])

        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(Session.self, from: data)
    }

    func sendMessage(sessionId: String, message: String) async throws {
        let url = URL(string: "\(baseURL)/api/chat/send")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode([
            "session_id": sessionId,
            "message": message
        ])

        let (_, _) = try await URLSession.shared.data(for: request)
    }
}
```

### Android (Kotlin)

```kotlin
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.MediaType.Companion.toMediaType
import com.google.gson.Gson

data class Session(
    val id: String,
    val title: String,
    val created_at: String,
    val updated_at: String,
    val messages: List<Message>
)

data class Message(
    val role: String,
    val content: String,
    val timestamp: String
)

class EOPFAPIClient {
    private val baseUrl = "http://localhost:8000"
    private val client = OkHttpClient()
    private val gson = Gson()

    suspend fun createSession(): Session = withContext(Dispatchers.IO) {
        val json = """{"title": "Android App Session"}"""
        val body = json.toRequestBody("application/json".toMediaType())

        val request = Request.Builder()
            .url("$baseUrl/api/sessions")
            .post(body)
            .build()

        client.newCall(request).execute().use { response ->
            gson.fromJson(response.body?.string(), Session::class.java)
        }
    }

    suspend fun sendMessage(sessionId: String, message: String) = withContext(Dispatchers.IO) {
        val json = gson.toJson(mapOf(
            "session_id" to sessionId,
            "message" to message
        ))
        val body = json.toRequestBody("application/json".toMediaType())

        val request = Request.Builder()
            .url("$baseUrl/api/chat/send")
            .post(body)
            .build()

        client.newCall(request).execute()
    }
}
```

## Configuration

The API server is configured via `src/config.yaml`:

```yaml
api:
  host: "0.0.0.0"          # Listen on all interfaces
  port: 8000                # API port
  cors_origins:             # Allowed CORS origins
    - "http://localhost:5173"
    - "http://localhost:3000"
    - "http://localhost:8080"  # Add your app's origin here
  session_storage_dir: ".sessions"
  max_sessions_per_user: 50
```

To allow your app to access the API, add its origin to the `cors_origins` list.

## Authentication

The current API does not include authentication. For production use, you should add:

1. **API Keys**: Add an API key middleware
2. **JWT Tokens**: Implement JWT-based authentication
3. **OAuth2**: Use OAuth2 for third-party apps
4. **Rate Limiting**: Add rate limiting to prevent abuse

Example middleware for API keys:

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API Key")
```

## Deployment

The API can be deployed to:

- **Cloud platforms**: AWS, Google Cloud, Azure
- **PaaS**: Heroku, Railway, Render
- **Containers**: Docker, Kubernetes
- **VPS**: DigitalOcean, Linode, Vultr

Example Dockerfile:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src ./src

# Install dependencies
RUN uv sync

# Expose port
EXPOSE 8000

# Run API server
CMD ["uv", "run", "python", "src/api_server.py"]
```

Build and run:

```bash
docker build -t eopf-api .
docker run -p 8000:8000 --env-file .env eopf-api
```

## Next Steps

- Explore the OpenAPI documentation at http://localhost:8000/docs
- Check out the [React frontend](../frontend/) for a web UI example
- Read the [Architecture documentation](ARCHITECTURE.md) for system internals
- See [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md) for all configuration options
