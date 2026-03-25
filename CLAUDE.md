# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **MCP (Model Context Protocol) server** that provides tools to interact with the **EOPF STAC catalog** for Earth Observation data retrieval. The project includes multiple interfaces:

### Backend Components
1. **MCP Server** ([src/main.py](src/main.py)) - Core server with 7 STAC query tools
2. **LLM Provider Abstraction** ([src/llm_provider.py](src/llm_provider.py)) - Supports Claude API, OVH AI Endpoints, and local Ollama
3. **FastAPI REST API** ([src/api_server.py](src/api_server.py)) - **Standalone API server** that can run independently with `uv run`
4. **Chat Handler** ([src/chat_handler.py](src/chat_handler.py)) - Shared logic for MCP/LLM interactions
5. **Session Store** ([src/session_store.py](src/session_store.py)) - JSON-based chat session persistence

### Frontend Interfaces
1. **Gradio Web UI** ([src/gradio_app.py](src/gradio_app.py)) - Simple chat interface (port 7860)
2. **React Frontend** ([frontend/](frontend/)) - Modern Vite/React SPA (port 5173)
3. **Next.js Chatbot** ([chatbot/](chatbot/)) - Full-featured Next.js app with database (port 3000)

## Choosing an Interface

The project provides **6 different ways** to interact with the MCP server:

| Interface | Use Case | Tech Stack | Port | Runs Standalone |
|-----------|----------|------------|------|-----------------|
| **Gradio UI** | Quick demos, simplest setup | Python/Gradio | 7860 | ✅ Yes (`uv run`) |
| **FastAPI REST API** | **Standalone API server** for any client | FastAPI + SSE | 8000 | ✅ Yes (`uv run`) |
| **FastAPI + React** | Modern web app, customizable UI | FastAPI + Vite/React | 8000 + 5173 | Needs frontend |
| **Next.js Chatbot** | Production-ready, full features | Next.js + AI SDK | 3000 | ✅ Yes (`pnpm`) |
| **Claude Desktop** | Native integration with Claude app | MCP stdio | - | ✅ Yes |
| **CLI Chat** | Terminal-based interaction | Python | - | ✅ Yes (`uv run`) |

**Recommendations**:
- **Development/Testing**: Gradio UI (fastest to start, port 7860)
- **API-only (no frontend)**: FastAPI REST API standalone (perfect for integrations, mobile apps, port 8000)
- **Best Web Experience**: FastAPI + React (markdown tables, syntax highlighting, map item selector, ports 8000 + 5173)
- **Production Deployment**: Next.js chatbot (includes database, auth-ready, port 3000) OR deploy React frontend ([docs/DEPLOY_FRONTEND.md](docs/DEPLOY_FRONTEND.md))
- **Claude App**: MCP server standalone (add to Claude Desktop config)
- **Scripting/Automation**: CLI chat

**For online deployment**: See [docs/DEPLOY_FRONTEND.md](docs/DEPLOY_FRONTEND.md) - Includes Cloudflare Tunnel (5 min), Vercel (10 min), Railway, and VPS options.

## Common Commands

### Running Different Interfaces

```bash
# 1. Gradio Web UI (simplest, port 7860)
uv run python src/gradio_app.py

# 2. FastAPI REST API (standalone, port 8000)
# Can be used WITHOUT the React frontend - it's a complete API server
uv run python src/api_server.py

# 3. FastAPI + React Frontend (modern web app, ports 8000 + 5173)
# Terminal 1: Start FastAPI backend
uv run python src/api_server.py

# Terminal 2: Start React dev server
cd frontend
npm install  # First time only
npm run dev

# 4. Next.js Chatbot (full-featured, port 3000)
cd chatbot
pnpm install  # First time only
pnpm dev

# 5. MCP Server standalone (for Claude Desktop integration)
uv run python src/main.py

# 6. Terminal chat client
uv run python src/chat_client.py
```

### Testing MCP Tools

```bash
# Test MCP server with mcp-cli (if available)
mcp list-tools
mcp call-tool list_collections
```

### Testing the FastAPI Server

```bash
# 1. Start the API server
uv run python src/api_server.py

# 2. In another terminal, test the endpoints
# Health check
curl http://localhost:8000/

# View OpenAPI docs
open http://localhost:8000/docs  # or visit in browser

# Create a session
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Session"}'

# List sessions
curl http://localhost:8000/api/sessions

# Test with httpie (if installed)
http POST http://localhost:8000/api/sessions title="My Chat"
```

### Dependencies

```bash
# Install dependencies (uv manages everything)
uv sync

# Add new dependency
uv add package-name

# Update dependencies
uv lock --upgrade
```

## Architecture Overview

### Multi-Process Architecture

The architecture varies by interface but follows this general pattern:

**Gradio Interface** (3 processes):
1. **Gradio Process** - Main thread (web server) + background thread (async MCP operations)
2. **MCP Server Process** - Subprocess via stdio, handles STAC catalog queries
3. **LLM Provider** - External API (Claude/OVH) or local server (Ollama)

**FastAPI + React Interface** (4 processes):
1. **FastAPI Server** (port 8000) - REST API backend with CORS
2. **React Dev Server** (port 5173) - Vite development server
3. **MCP Server Process** - Same subprocess pattern as Gradio
4. **LLM Provider** - Same as above

**Next.js Chatbot** (separate architecture):
- Full-featured Next.js app with its own database (Drizzle ORM)
- Uses AI SDK for streaming responses
- Independent deployment with its own MCP integration

**Key Characteristics**:
- All interfaces use **stdio communication** with MCP server subprocess
- MCP session initialized once and kept alive for app lifetime
- FastAPI uses **SSE (Server-Sent Events)** for streaming responses
- Session storage in `.sessions/` directory (JSON files)

### Critical Threading Pattern

**IMPORTANT**: The Gradio app uses `run_coroutine_threadsafe()` to bridge sync/async execution:

```python
# In gradio_app.py:
# Main thread (sync) -> Background thread (async) -> MCP session
future = asyncio.run_coroutine_threadsafe(
    self.chat(message, history),
    self.loop
)
return future.result(timeout=120)
```

This pattern prevents blocking the Gradio UI while waiting for async MCP tool calls.

### LLM Provider Abstraction

The system uses a **factory pattern** to select LLM providers at runtime:

```python
# In llm_provider.py:
def create_llm_provider() -> LLMProvider:
    config = get_config()
    if config.llm_provider == "claude":
        return ClaudeProvider(api_key=...)
    elif config.llm_provider == "ovh":
        return OVHProvider(api_token=...)
    elif config.llm_provider == "local":
        return OllamaProvider(base_url=...)
```

All providers implement the same interface:
- `async create_message(messages, tools)` - Send request to LLM
- `format_tool_response(response)` - Extract tool_use blocks and text

**To switch LLM providers**: Edit `llm_provider` in [src/config.yaml](src/config.yaml). No code changes needed.

**Current default**: The config.yaml may be set to `ovh` or `local` depending on your setup. Check the file to see which provider is active.

### MCP Session Lifecycle

The MCP session is initialized once at startup and kept alive:

```python
# In gradio_app.py:
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        self.mcp_session = session
        # Keep session alive indefinitely
        await asyncio.Event().wait()
```

**Never close or recreate the MCP session** - it persists for the lifetime of the Gradio app.

## Configuration System

### Config Files

- [src/config.yaml](src/config.yaml) - All runtime configuration (LLM provider, API settings, ports)
- [.env](.env) - API keys and credentials (git-ignored, use [.env.example](.env.example) as template)
- [frontend/package.json](frontend/package.json) - React frontend dependencies (Vite, TailwindCSS, Leaflet)
- [chatbot/package.json](chatbot/package.json) - Next.js chatbot dependencies (AI SDK, Drizzle ORM)

### Important Config Structure

```python
# In config_loader.py:
class Config:
    llm_provider: str  # "claude", "ovh", or "local"
    claude_model: str
    claude_max_tokens: int
    ovh_base_url: str
    ovh_model: str
    local_llm_provider: str  # "ollama", "llamacpp", "vllm"
    ollama_base_url: str
    ollama_model: str

    # FastAPI settings
    api_host: str
    api_port: int
    cors_origins: list[str]
    session_storage_dir: str
    max_sessions_per_user: int

    # Gradio settings
    gradio_server_name: str
    gradio_server_port: int
    gradio_share: bool
```

**When adding new config fields**:
1. Add to [src/config.yaml](src/config.yaml)
2. Add property to `Config` class in [src/config_loader.py](src/config_loader.py)
3. Access via `self.config.field_name`

## MCP Tools Reference

All 7 tools are defined in [src/main.py](src/main.py):

| Tool Name | Purpose | Key Parameters |
|-----------|---------|----------------|
| `list_collections` | List all STAC collections | None |
| `get_collection` | Get collection details | `collection_id` |
| `search_items` | Search STAC items | `collections`, `bbox`, `datetime`, `limit` |
| `get_item` | Get specific item details | `collection_id`, `item_id` |
| `get_item_assets` | Get item's data files | `collection_id`, `item_id` |
| `get_zarr_urls` | Get Zarr URLs from search | `collections`, `bbox`, `datetime`, `limit` |
| `download_zarr_info` | Get Python code to access Zarr | `zarr_url` |

### Important Visualization Limitations

**⚠️ ONLY SENTINEL-2 L2A SUPPORTS VISUALIZATION**

- **Sentinel-2 L2A** is the ONLY product that can be visualized with Titiler and map interfaces
- **Sentinel-1** SAR (Synthetic Aperture Radar) data cannot be visualized
- **Sentinel-3** optical data cannot be visualized with Titiler
- The MCP server automatically detects product types and includes appropriate warnings in responses
- When users ask to visualize non-L2A data, inform them that only Sentinel-2 L2A is supported for map visualization

**⚠️ DO NOT SUGGEST VISUALIZATION UNLESS EXPLICITLY REQUESTED**

- **CRITICAL**: Only provide visualization instructions if the user explicitly asks to "visualize", "show on map", "display", or similar requests
- For general search/query/find requests, return metadata only - **do not** suggest visualization or provide item IDs for the test map
- Users should request visualization separately if they want it
- The `download_zarr_info` tool should **only** be called if users explicitly ask for download/access information, Python code, or "how to use this data"
- Default behavior: Return search results with metadata, dates, bounding boxes - nothing more

### Tool Implementation Pattern

```python
@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    catalog = get_catalog()  # pystac_client.Client

    if name == "tool_name":
        # 1. Extract arguments
        param = arguments["param_name"]

        # 2. Call STAC catalog
        results = catalog.search(...)

        # 3. Format response as dict
        result = {"key": "value"}

        # 4. Return as TextContent
        return [TextContent(type="text", text=str(result))]
```

**Important**: Always return `list[TextContent]` with `text=str(result)` - the LLM parses the string representation.

## Key Implementation Details

### STAC Catalog Connection

```python
# In main.py:
STAC_URL = "https://stac.core.eopf.eodc.eu"

def get_catalog():
    return pystac_client.Client.open(STAC_URL)
```

**Important**:
- The EOPF STAC catalog is **publicly accessible** and requires **NO authentication**
- The catalog is reopened for each tool call - this is intentional to avoid connection state issues
- Credentials (ACCESS_KEY_ID/SECRET_ACCESS_KEY) are only needed for downloading Zarr data from S3, not for STAC queries

### S3 Credentials Handling

```python
# In main.py - download_zarr_info tool:
def get_s3_credentials():
    return {
        "key": os.getenv("ACCESS_KEY_ID"),
        "secret": os.getenv("SECRET_ACCESS_KEY"),
    }
```

**Important**: S3 credentials are **OPTIONAL** and only used for:
- Downloading Zarr data via S3 URLs (`s3://eodata/...`)
- HTTPS Zarr URLs work without any credentials
- STAC catalog queries never require credentials (public API)

Credentials are loaded from `.env` and the generated code instructs users to load from their own `.env` file (no credential values are exposed).

### Async/Await Patterns

**All MCP operations are async**:

```python
# In gradio_app.py:
async def chat(self, message: str, history: list):
    # Call Claude API (async)
    response = await self.llm.create_message(messages, tools)

    # Call MCP tools (async)
    if tool_uses:
        for tool_use in tool_uses:
            result = await self.mcp_session.call_tool(...)
```

**Gradio wrapper is sync** - uses `run_coroutine_threadsafe()` to execute async code from sync context.

### Error Handling

The system has **multiple error boundaries**:

1. **MCP tool errors** - Caught and returned as `TextContent` with error message
2. **LLM API errors** - Caught in `chat()`, printed to console, returned to user
3. **History validation** - Invalid Gradio history entries are cleaned in `chat_wrapper()`
4. **Timeout handling** - 120s timeout on `future.result()` prevents hanging
5. **FastAPI errors** - HTTP exceptions with proper status codes

### Session Management

**Session storage** ([src/session_store.py](src/session_store.py)):
- Sessions saved as JSON files in `.sessions/` directory
- Each session has unique UUID
- Session model includes: id, title, created_at, updated_at, messages, metadata
- Supports multiple concurrent users (50 sessions per user max by default)

**Session lifecycle**:
```python
# Create session
session = session_store.create_session(title="My Chat")

# Add message
session_store.add_message(session_id, role="user", content="Hello")

# Get session
session = session_store.get_session(session_id)

# List sessions
sessions = session_store.list_sessions()
```

### Streaming Responses

**FastAPI** uses **Server-Sent Events (SSE)** for streaming:
```python
async def stream_response():
    yield f"event: message_start\ndata: {json.dumps({...})}\n\n"
    yield f"event: content_delta\ndata: {json.dumps({...})}\n\n"
    yield f"event: message_end\ndata: {json.dumps({...})}\n\n"

return StreamingResponse(stream_response(), media_type="text/event-stream")
```

**Next.js chatbot** uses Vercel AI SDK's native streaming (different pattern).

## Testing Approach

### Manual Testing via Gradio

```bash
uv run python src/gradio_app.py
# Open http://localhost:7860
# Type: "List all collections"
# Expected: Claude uses list_collections tool and displays results
```

### Testing Individual Tools

Add a test block in [src/main.py](src/main.py):

```python
if __name__ == "__main__":
    # Test mode
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        catalog = get_catalog()
        print(catalog.get_collections())
    else:
        asyncio.run(main())
```

Run: `uv run python src/main.py test`

### Testing LLM Providers

Change `llm_provider` in [src/config.yaml](src/config.yaml) and restart Gradio:

```yaml
llm_provider: "local"  # Test Ollama
llm_provider: "ovh"    # Test OVH
llm_provider: "claude" # Test Claude
```

## Common Issues & Solutions

### Issue: "BrokenResourceError" in MCP session

**Cause**: MCP server process crashed or connection lost.

**Solution**: Restart Gradio app. Check `main.py` for exceptions.

### Issue: Tools not available to LLM

**Cause**: Tools not properly formatted or LLM doesn't support tool use.

**Check**:
1. Verify `self.mcp_tools` is populated in Gradio app
2. Check LLM provider formats tools correctly (Claude uses native format, others use JSON schema)
3. For local LLMs, ensure model supports tool use (qwen3.5:35b recommended)

### Issue: "Too many values to unpack" in chat_wrapper

**Cause**: Invalid Gradio history format (should be list of `[user_msg, bot_msg]` tuples).

**Solution**: The code validates and cleans history in `chat_wrapper()`. If issue persists, add more validation.

### Issue: Empty/partial responses from local LLM

**Cause**: Model too small or doesn't understand tool use format.

**Solution**:
- Use larger model (qwen3.5:35b or qwen3.5:72b)
- Increase `max_tokens` in config.yaml
- Check OllamaProvider/OVHProvider tool formatting

### Issue: CORS errors in React frontend

**Cause**: FastAPI CORS configuration doesn't allow frontend origin.

**Solution**:
1. Check frontend runs on port listed in [src/config.yaml](src/config.yaml) `cors_origins`
2. Default ports: 5173, 5174, 3000
3. Add custom port to `api.cors_origins` list if using different port

### Issue: FastAPI can't find main.py

**Cause**: Running `api_server.py` from wrong directory.

**Solution**:
- Always run from project root: `uv run python src/api_server.py`
- Or from src/: `cd src && uv run python api_server.py`
- The code auto-detects the correct path to `main.py`

### Issue: Session not persisting across restarts

**Cause**: `.sessions/` directory not writable or sessions not being saved.

**Check**:
1. Verify `.sessions/` directory exists and is writable
2. Check `session_storage_dir` in [src/config.yaml](src/config.yaml)
3. Look for errors in console when calling session_store methods

### Issue: Frontend can't connect to backend

**Cause**: Backend not running or wrong port.

**Solution**:
1. Ensure FastAPI is running: `uv run python src/api_server.py`
2. Check backend is on port 8000 (or configured port)
3. Verify API URL in frontend matches: `http://localhost:8000`
4. Check CORS headers in browser DevTools Network tab

## Code Modification Guidelines

### Adding a New MCP Tool

1. Add tool definition in `list_tools()` in [src/main.py](src/main.py)
2. Add tool handler in `call_tool()` in [src/main.py](src/main.py)
3. Follow the pattern: extract args → query STAC → format result → return TextContent
4. Test with any interface (Gradio/FastAPI/chatbot)

### Adding a New LLM Provider

1. Create new class in [src/llm_provider.py](src/llm_provider.py) inheriting from `LLMProvider`
2. Implement `create_message()` and `format_tool_response()`
3. Add provider selection in `create_llm_provider()` factory
4. Add config section in [src/config.yaml](src/config.yaml)
5. Update [src/config_loader.py](src/config_loader.py) with new fields

### Using FastAPI as a Standalone API

The FastAPI server ([src/api_server.py](src/api_server.py)) is a **fully independent REST API** that can run without any frontend. It provides:

**REST Endpoints**:
```
GET  /                          - Health check
GET  /api/sessions              - List all chat sessions
POST /api/sessions              - Create new session
GET  /api/sessions/{id}         - Get session details
DELETE /api/sessions/{id}       - Delete session
POST /api/chat/send             - Send message to session
GET  /api/chat/stream/{id}      - Stream response via SSE
```

**Running standalone**:
```bash
uv run python src/api_server.py
# API available at http://localhost:8000
# Visit http://localhost:8000/docs for OpenAPI documentation
```

**Using the API** (example with curl):
```bash
# 1. Create a session
SESSION_ID=$(curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "My Chat"}' | jq -r '.id')

# 2. Send a message
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"List all collections\"}"

# 3. Stream the response
curl -N http://localhost:8000/api/chat/stream/$SESSION_ID
```

**See complete examples**:
- [examples/api_curl_example.sh](examples/api_curl_example.sh) - Complete bash/curl example
- [examples/api_client_example.py](examples/api_client_example.py) - Python client with SSE streaming
- [docs/API_USAGE.md](docs/API_USAGE.md) - Full API documentation with Python, JavaScript, iOS, and Android examples

**Key features**:
- Server-Sent Events (SSE) for streaming responses
- CORS enabled for frontend integration
- Session persistence in `.sessions/` directory
- Automatic MCP server initialization on startup
- OpenAPI/Swagger docs at `/docs`

### Working with FastAPI Backend (Development)

**Key files**:
- [src/api_server.py](src/api_server.py) - FastAPI routes and CORS configuration
- [src/chat_handler.py](src/chat_handler.py) - Shared MCP/LLM logic (used by both API and Gradio)
- [src/session_store.py](src/session_store.py) - Session persistence (JSON files in `.sessions/`)
- [src/models.py](src/models.py) - Pydantic models for requests/responses

**Adding new API endpoints**:
1. Define Pydantic models in [src/models.py](src/models.py)
2. Add route in [src/api_server.py](src/api_server.py)
3. Use `get_chat_handler()` to access MCP session
4. Return SSE stream for real-time responses (see `/api/chat/stream` endpoint)

### Working with React Frontend

**Structure** ([frontend/src/](frontend/src/)):
- `components/` - React components (ChatInterface, MessageList, AssistantMessage, etc.)
- `services/` - API client for FastAPI backend
- `context/` - React Context for state management
- `utils/` - Helper functions

**Tech stack**:
- Vite for build/dev server
- TailwindCSS for styling
- Leaflet for map visualization
- React Router for routing
- ReactMarkdown + remark-gfm for markdown table rendering
- react-syntax-highlighter for code syntax highlighting (100+ languages)

**Markdown Rendering**:
The React frontend uses `react-markdown` with GitHub Flavored Markdown (GFM) support. Assistant messages are rendered as markdown, which means:

- **Tables render beautifully** with borders, hover effects, and alternating row colors
- **Headers** (H1-H4) have proper hierarchy and styling
- **Code blocks** support syntax highlighting (100+ languages via react-syntax-highlighter)
- **Lists, blockquotes, and links** are properly formatted

**Recent Features**:
- **Map Item Selector**: Dropdown to select from search results + custom Item ID input field ([docs/MAP_ITEM_SELECTOR_FEATURE.md](docs/MAP_ITEM_SELECTOR_FEATURE.md))
- **Syntax Highlighting**: Python, JavaScript, Bash, JSON, YAML, SQL, R and 100+ more languages ([docs/SYNTAX_HIGHLIGHTING_EXAMPLES.md](docs/SYNTAX_HIGHLIGHTING_EXAMPLES.md))

**Important formatting guidelines**:
1. Use markdown tables for structured data (they render cleanly)
2. Minimize emoji usage (professional tone)
3. See [docs/RESPONSE_FORMATTING_GUIDE.md](docs/RESPONSE_FORMATTING_GUIDE.md) for formatting best practices
4. See [docs/MARKDOWN_RENDERING_EXAMPLES.md](docs/MARKDOWN_RENDERING_EXAMPLES.md) for visual examples

**Custom markdown components** are defined in [frontend/src/components/AssistantMessage.jsx](frontend/src/components/AssistantMessage.jsx) with consistent styling matching the Windows 95 theme.

**Making API calls**:
```javascript
// In frontend/src/services/api.js
const response = await fetch('http://localhost:8000/send_message', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ session_id, message })
});
```

### Working with Next.js Chatbot

The chatbot is a **separate project** with its own architecture:
- Built with Next.js App Router
- Uses Vercel AI SDK for streaming
- Drizzle ORM for database (SQLite/PostgreSQL)
- Independent MCP integration

**To modify chatbot**: Work within the [chatbot/](chatbot/) directory as a separate codebase.

### Modifying STAC Queries

**All STAC logic is in [src/main.py](src/main.py)** - search for `catalog.search()` calls.

Common parameters:
- `bbox=[west, south, east, north]` (WGS84 coordinates)
- `datetime="2023-01-01/2023-12-31"` (ISO 8601 range)
- `collections=["SENTINEL-2-L1C"]` (collection IDs)
- `max_items=10` (result limit)

Refer to [pystac-client documentation](https://pystac-client.readthedocs.io/) for advanced queries.

## Project Structure

```
eof-mcp/
├── src/                    # Python backend
│   ├── main.py            # MCP server (7 STAC tools)
│   ├── api_server.py      # FastAPI backend for React
│   ├── gradio_app.py      # Gradio web interface
│   ├── chat_handler.py    # Shared MCP/LLM logic
│   ├── llm_provider.py    # LLM abstraction (Claude/OVH/Ollama)
│   ├── session_store.py   # JSON session persistence
│   ├── models.py          # Pydantic models
│   ├── config_loader.py   # Config management
│   ├── chat_client.py     # CLI chat client
│   └── config.yaml        # Runtime configuration
├── frontend/              # React SPA (Vite + TailwindCSS)
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API client
│   │   ├── context/       # State management
│   │   └── utils/         # Helpers
│   └── package.json
├── chatbot/               # Next.js full-featured chatbot
│   ├── app/               # Next.js App Router
│   ├── components/        # UI components
│   ├── lib/               # Database & utilities
│   └── package.json
├── docs/                  # Documentation
│   ├── ARCHITECTURE.md    # System diagrams
│   ├── QUICK_START.md     # Getting started guide
│   ├── API_USAGE.md       # FastAPI standalone usage guide
│   ├── LOCAL_LLM_SETUP.md # Ollama setup
│   └── OVH_SETUP.md       # OVH AI Endpoints setup
├── examples/              # Example code
│   ├── api_client_example.py  # Python API client example
│   └── api_curl_example.sh    # Curl/bash API example
├── .sessions/             # Session storage (git-ignored)
├── .env                   # API keys (git-ignored)
└── pyproject.toml         # Python dependencies (uv)
```

## Architecture Diagrams

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed Mermaid diagrams covering:
- System architecture
- Sequence diagrams (initialization, query flow, tool execution)
- Async event loop management
- LLM provider abstraction flow

## Documentation

### Getting Started
- [docs/QUICK_START.md](docs/QUICK_START.md) - Getting started guide
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick command reference card

### API & Deployment
- [docs/API_USAGE.md](docs/API_USAGE.md) - **Using the FastAPI server standalone** (Python, JavaScript, mobile apps)
- [docs/DEPLOY_FRONTEND.md](docs/DEPLOY_FRONTEND.md) - **Deploying frontend online** (Cloudflare Tunnel, Vercel, Railway, VPS)

### Response Formatting
- [docs/RESPONSE_FORMATTING_GUIDE.md](docs/RESPONSE_FORMATTING_GUIDE.md) - **How to format LLM responses** with markdown tables
- [docs/MARKDOWN_RENDERING_EXAMPLES.md](docs/MARKDOWN_RENDERING_EXAMPLES.md) - Examples of markdown rendering in frontend
- [docs/SYNTAX_HIGHLIGHTING_EXAMPLES.md](docs/SYNTAX_HIGHLIGHTING_EXAMPLES.md) - Syntax highlighting examples
- [docs/MAP_ITEM_SELECTOR_FEATURE.md](docs/MAP_ITEM_SELECTOR_FEATURE.md) - Map item selector feature guide
- [docs/EXAMPLE_QUERIES.md](docs/EXAMPLE_QUERIES.md) - Example STAC queries

### Configuration
- [docs/CONFIG_REFERENCE.md](docs/CONFIG_REFERENCE.md) - Configuration options
- [docs/LOCAL_LLM_SETUP.md](docs/LOCAL_LLM_SETUP.md) - Setting up Ollama
- [docs/OVH_SETUP.md](docs/OVH_SETUP.md) - OVH AI Endpoints configuration

## External Resources

- **EOPF STAC Catalog**: https://stac.core.eopf.eodc.eu
- **MCP Protocol Spec**: https://spec.modelcontextprotocol.io/
- **Claude API Docs**: https://docs.anthropic.com/
- **Ollama Models**: https://ollama.com/library
- **pystac-client**: https://pystac-client.readthedocs.io/
- **Vercel AI SDK**: https://sdk.vercel.ai/docs (for chatbot)
- **FastAPI**: https://fastapi.tiangolo.com/
- **Gradio**: https://gradio.app/
