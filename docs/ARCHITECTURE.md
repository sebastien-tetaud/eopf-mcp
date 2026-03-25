# System Architecture and Sequence Diagrams

## System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        GradioUI[Gradio Web UI<br/>Port 7860]
        ChatCLI[Chat CLI<br/>Terminal]
        ClaudeDesktop[Claude Desktop<br/>MCP Client]
    end

    subgraph "LLM Provider Layer"
        LLMProvider[LLM Provider<br/>Abstraction]
        ClaudeAPI[Claude API<br/>Anthropic]
        OVHAPI[OVH AI Endpoints<br/>EU Cloud]
        OllamaLocal[Ollama<br/>Local LLM]
    end

    subgraph "Integration Layer"
        MCPClient[MCP Client<br/>Session Handler]
    end

    subgraph "Service Layer"
        MCPServer[MCP Server<br/>main.py]
        STACTools[7 STAC Tools<br/>list, search, get, download]
    end

    subgraph "Data Layer"
        STACCatalog[EOPF STAC Catalog<br/>stac.core.eopf.eodc.eu]
        S3Storage[CDSE S3 Storage<br/>eodata.dataspace.copernicus.eu]
    end

    GradioUI --> LLMProvider
    ChatCLI --> LLMProvider
    LLMProvider -.->|config: claude| ClaudeAPI
    LLMProvider -.->|config: ovh| OVHAPI
    LLMProvider -.->|config: local| OllamaLocal
    ClaudeDesktop --> MCPClient
    LLMProvider --> MCPClient
    MCPClient --> MCPServer
    MCPServer --> STACTools
    STACTools --> STACCatalog
    STACTools --> S3Storage

    style GradioUI fill:#e1f5ff
    style LLMProvider fill:#fff9c4
    style ClaudeAPI fill:#fff4e1
    style OVHAPI fill:#e1f5ff
    style OllamaLocal fill:#f1f8e9
    style MCPServer fill:#e8f5e9
    style STACCatalog fill:#f3e5f5
```

### Detailed Component Architecture

```mermaid
graph LR
    subgraph "Gradio App Process"
        MainThread[Main Thread<br/>Gradio Server]
        BGThread[Background Thread<br/>Event Loop]
        MCPSession[MCP Session<br/>stdio_client]

        MainThread -->|run_coroutine_threadsafe| BGThread
        BGThread --> MCPSession
    end

    subgraph "MCP Server Process"
        MCPMain[main.py<br/>MCP Server]
        ToolRegistry[Tool Registry<br/>7 Tools]
        STACClient[STAC Client<br/>pystac_client]

        MCPMain --> ToolRegistry
        ToolRegistry --> STACClient
    end

    MCPSession -->|stdio| MCPMain

    style MainThread fill:#ffebee
    style BGThread fill:#e8f5e9
    style MCPMain fill:#e3f2fd
```

### Data Flow Architecture

```mermaid
flowchart TD
    Start([User Query]) --> GradioInput[Gradio Chat Input]
    GradioInput --> ChatWrapper[chat_wrapper<br/>Sync Function]
    ChatWrapper --> ValidateHistory{Validate<br/>History?}
    ValidateHistory -->|Valid| RunCoroutine[run_coroutine_threadsafe]
    ValidateHistory -->|Invalid| CleanHistory[Clean History]
    CleanHistory --> RunCoroutine

    RunCoroutine --> BGLoop[Background Event Loop]
    BGLoop --> ChatMethod[chat method<br/>Async]
    ChatMethod --> BuildMessages[Build Message History]
    BuildMessages --> SelectProvider{LLM<br/>Provider?}
    SelectProvider -->|claude| ClaudeCall[Claude API Call]
    SelectProvider -->|ovh| OVHCall[OVH API Call]
    SelectProvider -->|local| OllamaCall[Ollama API Call]

    ClaudeCall --> MergeResponses[Unified Response]
    OVHCall --> MergeResponses
    OllamaCall --> MergeResponses

    MergeResponses --> CheckTools{Tool Use<br/>Requested?}
    CheckTools -->|Yes| CallTool[Call MCP Tool]
    CallTool --> MCPServer[MCP Server<br/>Execute Tool]
    MCPServer --> STACQuery[Query STAC Catalog]
    STACQuery --> ToolResult[Tool Result]
    ToolResult --> MergeResponses

    CheckTools -->|No| FinalResponse[Final Text Response]
    FinalResponse --> FormatOutput[Format with Tool Info]
    FormatOutput --> Return([Return to User])

    style SelectProvider fill:#fff9c4
    style ClaudeCall fill:#fff4e1
    style OVHCall fill:#e1f5ff
    style OllamaCall fill:#f1f8e9
    style MCPServer fill:#e8f5e9
    style STACQuery fill:#f3e5f5
```

### LLM Provider Abstraction Architecture

```mermaid
graph TB
    subgraph "Application Layer"
        GradioApp[Gradio App<br/>gradio_app.py]
        ConfigFile[config.yaml<br/>LLM Provider Config]
    end

    subgraph "Abstraction Layer - llm_provider.py"
        Factory[create_llm_provider<br/>Factory Function]
        BaseProvider[LLMProvider<br/>Abstract Base Class]
    end

    subgraph "Provider Implementations"
        ClaudeImpl[ClaudeProvider<br/>Anthropic SDK]
        OVHImpl[OVHProvider<br/>OpenAI-compatible]
        OllamaImpl[OllamaProvider<br/>Local HTTP API]
    end

    subgraph "External APIs"
        ClaudeAPI[Claude API<br/>api.anthropic.com]
        OVHAPI[OVH AI Endpoints<br/>endpoints.kepler.ai.cloud.ovh.net]
        OllamaAPI[Ollama Server<br/>localhost:11434]
    end

    GradioApp --> ConfigFile
    GradioApp --> Factory
    ConfigFile -.->|llm_provider: claude/ovh/local| Factory
    Factory --> BaseProvider
    BaseProvider -.->|implements| ClaudeImpl
    BaseProvider -.->|implements| OVHImpl
    BaseProvider -.->|implements| OllamaImpl

    ClaudeImpl --> ClaudeAPI
    OVHImpl --> OVHAPI
    OllamaImpl --> OllamaAPI

    style Factory fill:#fff9c4
    style BaseProvider fill:#ffe0b2
    style ClaudeImpl fill:#fff4e1
    style OVHImpl fill:#e1f5ff
    style OllamaImpl fill:#f1f8e9
```

**LLM Provider Interface:**
```python
class LLMProvider(ABC):
    @abstractmethod
    async def create_message(messages, tools=None) -> Response

    @abstractmethod
    def format_tool_response(response) -> (tool_uses, text)
```

**Configuration-Based Selection:**
- `llm_provider: "claude"` → ClaudeProvider (Anthropic API)
- `llm_provider: "ovh"` → OVHProvider (OVH AI Endpoints)
- `llm_provider: "local"` → OllamaProvider (Local Ollama)

**Model Options:**
- **Claude**: opus-4-6, sonnet-4-5, haiku-4
- **OVH**: Llama-3.1-8B-Instruct, Mistral-7B-Instruct-v0.3
- **Ollama**: qwen3.5:35b, llama3.1, mistral, etc.

## Sequence Diagrams

### 1. Gradio App Initialization

```mermaid
sequenceDiagram
    participant User
    participant Main as main()
    participant App as STACGradioApp
    participant Thread as Background Thread
    participant Loop as Event Loop
    participant MCP as MCP Server Process

    User->>Main: uv run python gradio_app.py
    Main->>Main: Load config.yaml
    Main->>Main: Load .env (API keys)
    Main->>Main: create_llm_provider()
    Note over Main: Selects Claude/OVH/Ollama<br/>based on config
    Main->>App: Initialize STACGradioApp
    Main->>Thread: Start background thread
    Thread->>Loop: Create new event loop
    Loop->>Loop: loop.run_forever()

    Main->>Loop: run_coroutine_threadsafe(setup_mcp)
    Loop->>MCP: Start MCP server subprocess
    MCP->>MCP: Initialize STAC connection
    MCP-->>Loop: Connection established
    Loop->>App: Store mcp_session & tools

    Main->>Main: Create Gradio interface
    Main->>User: Launch web UI (port 7860)

    Note over User,MCP: System ready for queries
```

### 2. User Query Flow (with Tool Use)

```mermaid
sequenceDiagram
    participant User
    participant Gradio as Gradio UI
    participant Wrapper as chat_wrapper
    participant Loop as Event Loop
    participant Chat as chat() method
    participant Provider as LLM Provider
    participant LLM as LLM API<br/>(Claude/OVH/Ollama)
    participant MCP as MCP Server
    participant STAC as STAC Catalog

    User->>Gradio: "Get Zarr URLs for Sentinel-2..."
    Gradio->>Wrapper: chat_wrapper(message, history)
    Wrapper->>Wrapper: Validate history format

    Wrapper->>Loop: run_coroutine_threadsafe(chat)
    Loop->>Chat: Execute async chat()
    Chat->>Chat: Build message history

    Chat->>Provider: create_message(messages, tools)
    Provider->>LLM: API call with tools
    LLM-->>Provider: Response with tool_use
    Provider-->>Chat: Formatted response

    Chat->>Chat: Extract tool_use blocks
    loop For each tool
        Chat->>MCP: call_tool("get_zarr_urls", args)
        MCP->>STAC: Search catalog with filters
        STAC-->>MCP: Items with Zarr assets
        MCP->>MCP: Filter Zarr URLs
        MCP-->>Chat: Tool result
    end

    Chat->>Chat: Append tool results to messages
    Chat->>Provider: create_message(with tool results)
    Provider->>LLM: API call with results
    LLM-->>Provider: Final text response
    Provider-->>Chat: Formatted response

    Chat-->>Loop: Return formatted response
    Loop-->>Wrapper: Response ready
    Wrapper-->>Gradio: Display response
    Gradio-->>User: Show results with tool info
```

### 3. STAC Search and Download Flow

```mermaid
sequenceDiagram
    participant User
    participant Gradio
    participant LLM as LLM Provider
    participant MCP as MCP Server
    participant STAC as STAC Catalog
    participant S3 as S3 Storage

    User->>Gradio: "Search Sentinel-2 over Italy"
    Gradio->>LLM: Natural language query

    LLM->>MCP: search_items(collections, bbox, datetime)
    MCP->>STAC: catalog.search(...)
    STAC-->>MCP: List of matching items
    MCP-->>LLM: Item metadata (JSON)
    LLM-->>User: "Found 5 items matching..."

    User->>Gradio: "Get Zarr URLs"
    Gradio->>LLM: Follow-up query

    LLM->>MCP: get_zarr_urls(collections, bbox, datetime)
    MCP->>STAC: catalog.search(...)
    STAC-->>MCP: Items with assets
    MCP->>MCP: Filter for Zarr assets
    MCP-->>LLM: Zarr URLs + metadata
    LLM-->>User: "s3://eodata/..."

    User->>Gradio: "How to download?"
    Gradio->>LLM: Download instructions request

    LLM->>MCP: download_zarr_info(zarr_url)
    MCP->>MCP: Load S3 credentials from .env
    MCP->>MCP: Generate Python code
    MCP-->>LLM: Code snippet + instructions
    LLM-->>User: Python code with credentials

    User->>User: Copy code and run locally
    User->>S3: Access Zarr with s3fs
    S3-->>User: Stream/download data
```

### 4. MCP Tool Execution Detail

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant Server as MCP Server (main.py)
    participant Handler as call_tool()
    participant STAC as STAC Catalog
    participant Env as Environment (.env)

    Client->>Server: JSONRPCRequest(tool_name, args)
    Server->>Handler: Dispatch to handler

    alt Tool: search_items
        Handler->>STAC: catalog.search(bbox, datetime, collections)
        STAC-->>Handler: Search results
        Handler->>Handler: Format as dict
        Handler-->>Server: TextContent(JSON string)

    else Tool: get_zarr_urls
        Handler->>STAC: catalog.search(filters)
        STAC-->>Handler: Items with assets
        Handler->>Handler: Filter for Zarr assets only
        Handler-->>Server: TextContent(Zarr URLs + metadata)

    else Tool: download_zarr_info
        Handler->>Env: Load ACCESS_KEY_ID, SECRET_ACCESS_KEY
        Env-->>Handler: Credentials
        Handler->>Handler: Generate Python code template
        Handler->>Handler: Inject credentials into code
        Handler-->>Server: TextContent(Code + instructions)

    else Tool: list_collections
        Handler->>STAC: catalog.get_collections()
        STAC-->>Handler: All collections
        Handler->>Handler: Extract metadata
        Handler-->>Server: TextContent(Collections list)
    end

    Server-->>Client: JSONRPCResponse(result)
```

### 5. Async Event Loop Management

```mermaid
sequenceDiagram
    participant Main as Main Thread
    participant BG as Background Thread
    participant Loop as Event Loop
    participant MCP as MCP Session
    participant Server as MCP Server Process

    Note over Main,Server: Initialization Phase
    Main->>BG: Start thread (daemon=True)
    BG->>Loop: asyncio.new_event_loop()
    BG->>Loop: set_event_loop(loop)
    BG->>Loop: loop.run_forever()

    Note over Loop: Loop now running forever

    Main->>Loop: run_coroutine_threadsafe(setup_mcp)
    Loop->>Server: Start subprocess (uv run main.py)
    Loop->>MCP: stdio_client() context enter
    Loop->>MCP: ClientSession() context enter
    MCP->>Server: Initialize connection
    Server-->>MCP: Ready
    Loop->>MCP: list_tools()
    MCP-->>Loop: 7 tools available
    Loop->>Loop: await asyncio.Event().wait()

    Note over Loop,MCP: Session kept alive indefinitely

    Note over Main,Server: Request Phase
    Main->>Loop: run_coroutine_threadsafe(chat)
    Loop->>MCP: call_tool()
    MCP->>Server: Tool request
    Server-->>MCP: Tool result
    MCP-->>Loop: Result
    Loop-->>Main: future.result()

    Note over Main: Response returned to Gradio
```

### 6. Error Handling Flow

```mermaid
sequenceDiagram
    participant User
    participant Wrapper as chat_wrapper
    participant Loop as Event Loop
    participant Chat as chat()
    participant Claude as Claude API
    participant MCP as MCP Server

    User->>Wrapper: Send message

    alt Invalid History Format
        Wrapper->>Wrapper: Validate history
        Wrapper->>Wrapper: Clean invalid entries
        Note over Wrapper: Prevents "too many values to unpack"
    end

    Wrapper->>Loop: run_coroutine_threadsafe

    alt Timeout
        Loop-->>Wrapper: TimeoutError (120s)
        Wrapper-->>User: "Request timed out..."
    end

    alt Claude API Error
        Loop->>Claude: messages.create()
        Claude-->>Loop: APIError
        Loop->>Chat: Exception
        Chat->>Chat: print(traceback)
        Chat-->>Loop: Error message
        Loop-->>Wrapper: Error string
        Wrapper-->>User: "❌ Error: ... Please rephrase..."
    end

    alt MCP Connection Lost
        Loop->>MCP: call_tool()
        MCP-->>Loop: BrokenResourceError
        Loop->>Chat: Exception
        Chat-->>Wrapper: Error message
        Wrapper-->>User: "❌ Error: ... try refreshing"
    end

    alt Success
        Loop->>Claude: API call
        Claude-->>Loop: Success response
        Loop-->>Wrapper: Result
        Wrapper-->>User: Display response
    end
```

## Component Details

### MCP Server Tools

| Tool Name | Input | Output | STAC Operation |
|-----------|-------|--------|----------------|
| `list_collections` | None | List of collections | `catalog.get_collections()` |
| `get_collection` | collection_id | Collection metadata | `catalog.get_collection(id)` |
| `search_items` | bbox, datetime, collections, query | Items matching filters | `catalog.search(...)` |
| `get_item` | collection_id, item_id | Full item metadata | `collection.get_item(id)` |
| `get_item_assets` | collection_id, item_id | Asset URLs and types | `item.assets` |
| `get_zarr_urls` | bbox, datetime, collections | Filtered Zarr URLs | `catalog.search()` + filter |
| `download_zarr_info` | zarr_url | Python code + credentials | Load from .env |

### Async Architecture Pattern

```
┌─────────────────────────────────────┐
│         Main Thread (Sync)          │
│  ┌──────────────────────────────┐  │
│  │      Gradio Server           │  │
│  │  - HTTP requests             │  │
│  │  - Chat UI rendering         │  │
│  └────────────┬─────────────────┘  │
│               │                     │
│        chat_wrapper(sync)           │
│               │                     │
│               │ run_coroutine_      │
│               │   threadsafe()      │
└───────────────┼─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│    Background Thread (Async)        │
│  ┌──────────────────────────────┐  │
│  │     Event Loop               │  │
│  │  - Runs forever              │  │
│  │  - Handles MCP async ops     │  │
│  └────────────┬─────────────────┘  │
│               │                     │
│        chat() async method          │
│               │                     │
│  ┌────────────▼─────────────────┐  │
│  │    MCP Session (Async)       │  │
│  │  - stdio_client context      │  │
│  │  - ClientSession context     │  │
│  │  - Kept alive with Event()   │  │
│  └────────────┬─────────────────┘  │
└───────────────┼─────────────────────┘
                │ stdio
                ▼
┌─────────────────────────────────────┐
│    MCP Server Process (Subprocess)  │
│  ┌──────────────────────────────┐  │
│  │      main.py                 │  │
│  │  - Stdio communication       │  │
│  │  - Tool execution            │  │
│  │  - STAC queries              │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Local Development"
        DevMachine[Developer Machine]
        LocalGradio[Gradio App<br/>localhost:7860]
        LocalMCP[MCP Server Process]

        DevMachine --> LocalGradio
        LocalGradio --> LocalMCP
    end

    subgraph "Claude Desktop Integration"
        DesktopApp[Claude Desktop App]
        DesktopMCP[MCP Server<br/>via config.json]

        DesktopApp --> DesktopMCP
    end

    subgraph "External Services"
        STACEndpoint[EOPF STAC Catalog<br/>stac.core.eopf.eodc.eu]
        S3Endpoint[CDSE S3<br/>eodata.dataspace.copernicus.eu]
        AnthropicAPI[Claude API<br/>api.anthropic.com]
    end

    LocalMCP --> STACEndpoint
    LocalMCP --> S3Endpoint
    LocalGradio --> AnthropicAPI
    DesktopMCP --> STACEndpoint
    DesktopMCP --> S3Endpoint
    DesktopApp --> AnthropicAPI

    style LocalGradio fill:#e1f5ff
    style AnthropicAPI fill:#fff4e1
    style STACEndpoint fill:#f3e5f5
```

## Security Architecture

```mermaid
graph LR
    subgraph "Credential Storage"
        EnvFile[.env file<br/>git-ignored]
        EnvVars[Environment Variables]
    end

    subgraph "Application Layer"
        LoadEnv[load_dotenv]
        MCPServer[MCP Server]
        GradioApp[Gradio App]
    end

    subgraph "External APIs"
        ClaudeAPI[Claude API<br/>ANTHROPIC_API_KEY]
        OVHAPI[OVH AI Endpoints<br/>OVH_AI_ENDPOINTS_ACCESS_TOKEN]
        OllamaAPI[Ollama Server<br/>No credentials]
        S3API[S3 Storage<br/>ACCESS_KEY_ID<br/>SECRET_ACCESS_KEY]
    end

    EnvFile --> LoadEnv
    EnvVars --> LoadEnv
    LoadEnv --> MCPServer
    LoadEnv --> GradioApp

    GradioApp -->|config: claude| ClaudeAPI
    GradioApp -->|config: ovh| OVHAPI
    GradioApp -->|config: local| OllamaAPI
    MCPServer -->|S3 Protocol| S3API

    style EnvFile fill:#ffebee
    style ClaudeAPI fill:#fff4e1
    style OVHAPI fill:#e1f5ff
    style OllamaAPI fill:#f1f8e9
    style S3API fill:#e8f5e9
```

## LLM Provider Comparison

| Feature | Claude API | OVH AI Endpoints | Ollama (Local) |
|---------|-----------|------------------|----------------|
| **Quality** | Excellent | Good | Good |
| **Speed** | Fast | Fast | Medium (CPU-dependent) |
| **Cost** | $$$ (pay-per-token) | $ (pay-per-token) | Free |
| **Privacy** | Cloud (US) | Cloud (EU) | Local |
| **Tool Use** | Native support | JSON parsing | JSON parsing |
| **Setup** | API key | API token | Install + model download |
| **Offline** | No | No | Yes |
| **Models** | opus-4-6, sonnet-4-5, haiku-4 | Llama-3.1-8B, Mistral-7B | qwen3.5:35b, llama3.1, etc. |
| **RAM Required** | N/A | N/A | 8-48GB (model dependent) |
| **GDPR Compliant** | US servers | EU servers | Local only |

**Configuration:** Set `llm_provider` in [config.yaml](config.yaml)

## Performance Considerations

| Component | Optimization | Impact |
|-----------|-------------|--------|
| Event Loop | Dedicated background thread | Prevents blocking Gradio UI |
| MCP Session | Single persistent connection | Avoid reconnection overhead |
| Tool Calls | Async execution | Multiple tools can run concurrently |
| STAC Queries | Limit parameter (default: 10) | Control response size |
| Zarr Access | Lazy loading with xarray | Stream data instead of full download |
| LLM API Calls | 120s timeout | Prevent indefinite hangs |
| History Validation | Early validation in wrapper | Prevent cascading errors |
| **Ollama Models** | Larger models = better quality | qwen3.5:35b (23GB) recommended for quality |
| **OVH Models** | Llama-3.1-8B-Instruct | Better tool use than Mistral |

## Configuration Examples

### Using Claude API (Best Quality)
```yaml
llm_provider: "claude"
claude:
  model: "claude-opus-4-6"
  max_tokens: 4096
  temperature: 0.7
```

### Using OVH AI Endpoints (EU-Hosted, Lower Cost)
```yaml
llm_provider: "ovh"
ovh:
  base_url: "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1"
  model: "Llama-3.1-8B-Instruct"
  max_tokens: 4096
  temperature: 0.7
```

### Using Ollama (Local, Free)
```yaml
llm_provider: "local"
local_llm:
  provider: "ollama"
  ollama:
    base_url: "http://localhost:11434"
    model: "qwen3.5:35b"  # 35B parameters, 23GB download
  max_tokens: 4096
  temperature: 0.7
```

## Notes

- All diagrams use Mermaid syntax for rendering in Markdown viewers
- The architecture supports multiple concurrent users via Gradio's async handling
- MCP session remains open for the lifetime of the Gradio app
- Credentials are never exposed in logs or responses (partially masked in download_zarr_info)
- **STAC catalog URL**: https://stac.core.eopf.eodc.eu
- **LLM Provider** is configurable via `config.yaml` - no code changes needed to switch
- **Ollama models** - With 86GB RAM, can run up to qwen3.5:72b (48GB model)
- **Tool use quality** varies by provider: Claude (excellent) > OVH Llama (good) > Ollama (fair)
