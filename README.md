# EOPF STAC MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with tools to query and retrieve Earth Observation data from the [EOPF STAC catalog](https://stac.core.eopf.eodc.eu). Built with Python and designed for seamless integration with Claude, local LLMs, and other AI systems.

## Features

- **7 STAC Query Tools** - List collections, search items, retrieve Zarr URLs, and more
- **Multiple LLM Providers** - Works with Claude API, OVH AI Endpoints, or local Ollama models
- **6 Different Interfaces** - Gradio UI, FastAPI REST API, React frontend, Next.js chatbot, Claude Desktop, or CLI
- **No Authentication Required** - Public STAC catalog access (S3 credentials only needed for data downloads)
- **Production Ready** - Includes session management, streaming responses, and comprehensive error handling

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Optional: [Ollama](https://ollama.com/) for local LLM (or use Claude API)

### Installation

```bash
# Clone the repository
git clone git@github.com:sebastien-tetaud/eopf-mcp.git
cd eopf-mcp

# Install dependencies with uv
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys (if using Claude or OVH)
```

### Choose Your Interface

#### 1. FastAPI REST API (Standalone Server)

```bash
uv run python run_api.py
# API available at http://localhost:8000
# OpenAPI docs at http://localhost:8000/docs
```

Use this for mobile apps, integrations, or custom frontends. See [examples/](examples/) for client code.

#### 2. FastAPI + React Frontend (Best Web Experience)

```bash
# Terminal 1: Start backend
uv run python run_api.py

# Terminal 2: Start React frontend
cd frontend
npm install  # First time only
npm run dev  # Open http://localhost:5173
```

Modern web interface with markdown tables, syntax highlighting, and interactive maps.


#### 5. Claude Desktop Integration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "eopf-stac": {
      "command": "uv",
      "args": ["run", "python", "/path/to/eopf-mcp/src/eopf_mcp/mcp_server.py"]
    }
  }
}
```

#### 6. Terminal Chat Client

```bash
uv run python run_chat.py
```

## Configuration

All configuration is in [config/config.yaml](config/config.yaml). Key settings:

### LLM Provider Selection

```yaml
# Choose one: "claude", "ovh", or "local"
llm_provider: "local"
```

**Claude API** (Best quality, requires API key):
```yaml
llm_provider: "claude"
claude:
  model: "claude-opus-4-6"
  max_tokens: 4096
```

**OVH AI Endpoints** (EU-hosted, lower cost):
```yaml
llm_provider: "ovh"
ovh:
  model: "Llama-3.1-8B-Instruct"
  base_url: "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1"
```

**Local Ollama** (Free, private, offline):
```yaml
llm_provider: "local"
local_llm:
  provider: "ollama"
  ollama:
    model: "qwen3.5:35b"  # Recommended: 23GB RAM required
    base_url: "http://localhost:11434"
```

### API Keys

Add to `.env` (copy from `.env.example`):

```bash
# Claude API (only if using llm_provider: "claude")
ANTHROPIC_API_KEY=your-api-key-here

# OVH AI Endpoints (only if using llm_provider: "ovh")
OVH_AI_ENDPOINTS_ACCESS_TOKEN=your-token-here

# S3 Credentials (OPTIONAL - only for downloading Zarr data)
ACCESS_KEY_ID=your-access-key-here
SECRET_ACCESS_KEY=your-secret-key-here
```

**Note**: The STAC catalog is publicly accessible. No credentials are needed for queriesonly for downloading Zarr data from S3.

## Available MCP Tools

| Tool | Description | Example Use Case |
|------|-------------|------------------|
| `list_collections` | List all STAC collections | "What collections are available?" |
| `get_collection` | Get collection details | "Tell me about Sentinel-2 L2A" |
| `search_items` | Search for data items | "Find Sentinel-2 over Italy in June 2023" |
| `get_item` | Get specific item details | "Get details for item S2A_L2A_20230615..." |
| `get_item_assets` | Get item's downloadable files | "What files are in this item?" |
| `get_zarr_urls` | Get Zarr URLs from search | "Get Zarr URLs for Sentinel-3 over France" |
| `download_zarr_info` | Generate Python download code | "How do I download this Zarr data?" |

## Example Queries

Try these in any interface:

```
List all available collections

Search for Sentinel-2 L2A data over Paris from June 2023

Get Zarr URLs for Sentinel-3 OLCI over the Mediterranean Sea in July 2023

Show me how to download Zarr data for item ID S2A_L2A_20230615T103031_N0509_R108_T32TQM_20230615T140723
```

## Architecture

### Multi-Process Design

- **Gradio/FastAPI** - Main application server (web UI or REST API)
- **MCP Server** - Subprocess handling STAC catalog queries via stdio
- **LLM Provider** - External API (Claude/OVH) or local server (Ollama)

### Key Technologies

- **Backend**: Python 3.12, FastAPI, Gradio, MCP SDK, pystac-client
- **Frontend**: React + Vite, TailwindCSS, Leaflet maps, ReactMarkdown
- **Database**: JSON-based session storage (`data/sessions/` directory)
- **Streaming**: Server-Sent Events (SSE) for real-time responses

## Project Structure

```
eopf-mcp/
├── src/
│   └── eopf_mcp/            # Main Python package
│       ├── __init__.py
│       ├── mcp_server.py    # MCP server (7 STAC tools)
│       ├── api/             # FastAPI REST API
│       │   ├── server.py
│       │   └── models.py
│       ├── llm/             # LLM providers
│       │   ├── provider.py
│       │   └── config.py
│       ├── chat/            # Chat handlers
│       │   ├── handler.py
│       │   └── client.py
│       ├── storage/         # Session storage
│       │   └── session_store.py
├── frontend/                # React SPA
├── chatbot/                 # Next.js app
├── config/                  # Configuration files
│   ├── config.yaml          # Main config
│   └── config.example.yaml
├── data/                    # Runtime data (gitignored)
│   └── sessions/
├── docs/                    # Documentation
├── examples/                # Example code
├── run_api.py               # Entry point: API server
├── run_chat.py              # Entry point: Chat client
└── .env.example
```

## Documentation

- **[QUICK_START.md](docs/QUICK_START.md)** - Detailed setup and configuration guide
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture with diagrams
- **[API_USAGE.md](docs/API_USAGE.md)** - Using the FastAPI server standalone
- **[DEPLOY_FRONTEND.md](docs/DEPLOY_FRONTEND.md)** - Deploy React frontend online
- **[CLAUDE.md](CLAUDE.md)** - Development guide for AI assistants
- **[CONFIG_REFERENCE.md](docs/CONFIG_REFERENCE.md)** - Complete config reference
- **[LOCAL_LLM_SETUP.md](docs/LOCAL_LLM_SETUP.md)** - Ollama setup guide
- **[RESPONSE_FORMATTING_GUIDE.md](docs/RESPONSE_FORMATTING_GUIDE.md)** - LLM response formatting

## Development

### Adding a New MCP Tool

1. Add tool definition in `list_tools()` in [src/main.py](src/main.py)
2. Add tool handler in `call_tool()` in [src/main.py](src/main.py)
3. Follow the pattern: extract args � query STAC � format result � return TextContent
4. Test with any interface

### Adding a New LLM Provider

1. Create provider class in [src/llm_provider.py](src/llm_provider.py)
2. Implement `create_message()` and `format_tool_response()` methods
3. Add to factory function in `create_llm_provider()`
4. Add config section in [src/config.yaml](src/config.yaml)

### Running Tests

```bash
# Test individual MCP tools
uv run python src/main.py test

# Test FastAPI endpoints
uv run python src/api_server.py &
curl http://localhost:8000/
```

## Deployment

### Deploy React Frontend Online

See [docs/DEPLOY_FRONTEND.md](docs/DEPLOY_FRONTEND.md) for deployment guides:

- **Cloudflare Tunnel** (5 min) - Expose local server with HTTPS
- **Vercel** (10 min) - Deploy static frontend with backend proxy
- **Railway** - Deploy full stack with one command
- **VPS** - Traditional server deployment

### Deploy Next.js Chatbot

```bash
cd chatbot
pnpm build
pnpm start  # or deploy to Vercel
```

## Troubleshooting

### Common Issues

**"BrokenResourceError" in MCP session**
- Restart the application. MCP server subprocess crashed.

**Tools not available to LLM**
- Check `llm_provider` in config.yaml
- For local LLMs, use models that support tool use (qwen3.5:35b recommended)
- Verify tools are populated: check logs for "Available tools: 7"

**CORS errors in React frontend**
- Check frontend port is in `api.cors_origins` in config.yaml
- Default ports: 5173, 5174, 3000

**Empty responses from local LLM**
- Use larger model (qwen3.5:35b or qwen3.5:72b)
- Increase `max_tokens` in config.yaml
- Check model supports tool/function calling

**Session not persisting**
- Verify `.sessions/` directory exists and is writable
- Check `session_storage_dir` in config.yaml

### Getting Help

- Check [docs/](docs/) for detailed guides
- Review [CLAUDE.md](CLAUDE.md) for architecture details
- Open an issue on GitHub

## Important Notes

### Visualization Limitations

Only **Sentinel-2 L2A** products support visualization with Titiler and map interfaces:
- Sentinel-1 SAR data cannot be visualized
- Sentinel-3 optical data cannot be visualized with Titiler
- The system automatically detects product types and includes warnings

### S3 vs HTTPS Zarr Access

- **HTTPS URLs** (`https://eodata.dataspace.copernicus.eu/...`) work without credentials
- **S3 URLs** (`s3://eodata/...`) require ACCESS_KEY_ID and SECRET_ACCESS_KEY in `.env`
- STAC catalog queries never require credentials (public API)

## License

[Add your license here]

## Credits

Built with:
- [Model Context Protocol](https://spec.modelcontextprotocol.io/) by Anthropic
- [EOPF STAC Catalog](https://stac.core.eopf.eodc.eu) by EODC
- [pystac-client](https://pystac-client.readthedocs.io/) for STAC queries
- [FastAPI](https://fastapi.tiangolo.com/) for REST API
- [Gradio](https://gradio.app/) for web UI
- [Ollama](https://ollama.com/) for local LLM support

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Links

- **EOPF STAC Catalog**: https://stac.core.eopf.eodc.eu
- **MCP Protocol Spec**: https://spec.modelcontextprotocol.io/
- **Claude API Docs**: https://docs.anthropic.com/
- **Ollama Models**: https://ollama.com/library
