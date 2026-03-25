# Configuration Reference

Complete reference for `config.yaml` settings.

## Quick Start

```bash
# 1. Choose your LLM provider
# Edit config.yaml: llm_provider: "claude" or "local"

# 2. Set credentials (if using Claude)
# Edit .env: ANTHROPIC_API_KEY=your-key

# 3. Test configuration
uv run python test_config.py

# 4. Run Gradio app
uv run python gradio_app.py
```

## Configuration File: config.yaml

### LLM Provider Selection

```yaml
# Choose between Claude API, OVH AI Endpoints, or local LLM
# Options: "claude", "ovh", or "local"
llm_provider: "claude"
```

**When to use each:**
- **"claude"** - Best quality, requires API key, higher cost
- **"ovh"** - Good quality, EU-hosted, lower cost than Claude
- **"local"** - Free, private, works offline, requires local setup

### Claude API Configuration

```yaml
claude:
  model: "claude-opus-4-6"        # Claude model to use
  max_tokens: 4096                 # Maximum tokens in response
  temperature: 0.7                 # Creativity (0.0-1.0)
```

**Available Claude models:**
- `claude-opus-4-6` - Most capable (recommended)
- `claude-sonnet-4-5` - Balanced speed/quality
- `claude-haiku-4` - Fastest, cheapest

**API key:** Set in `.env` file as `ANTHROPIC_API_KEY`

### OVH AI Endpoints Configuration

```yaml
ovh:
  base_url: "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1"
  model: "Qwen3Guard-Gen-8B"     # Model name
  max_tokens: 4096                # Maximum tokens in response
  temperature: 0.7                # Creativity (0.0-1.0)
```

**Available models:**
- `Llama-3.1-8B-Instruct` - **Recommended** - Good instruction following
- `Mistral-7B-Instruct-v0.3` - Faster, alternative option
- ~~`Qwen3Guard-Gen-8B`~~ - Safety model, not for general use

**API token:** Set in `.env` file as `OVH_AI_ENDPOINTS_ACCESS_TOKEN`

**Setup:** See [OVH_SETUP.md](OVH_SETUP.md)

### Local LLM Configuration

```yaml
local_llm:
  provider: "ollama"              # Local LLM provider

  ollama:
    base_url: "http://localhost:11434"  # Ollama server URL
    model: "llama3.1"                    # Model name

  max_tokens: 4096                # Maximum tokens in response
  temperature: 0.7                # Creativity (0.0-1.0)
  top_p: 0.9                      # Nucleus sampling
```

**Ollama models to try:**
- `llama3.1` - Recommended, 8GB RAM
- `llama3.2` - Smaller, 4GB RAM
- `qwen2.5:14b` - More capable, 16GB RAM
- `mistral` - Alternative option

**Setup:** See [LOCAL_LLM_SETUP.md](LOCAL_LLM_SETUP.md)

### MCP Server Configuration

```yaml
mcp:
  stac_url: "https://stac.core.eopf.eodc.eu"  # STAC catalog URL
  default_search_limit: 10                      # Default max search results
```

**STAC URL:** Don't change unless using different catalog

### Gradio Configuration

```yaml
gradio:
  server_name: "0.0.0.0"    # Listen on all interfaces
  server_port: 7860          # Port number
  share: true                # Generate public Gradio link
```

**Common settings:**
- `server_name: "127.0.0.1"` - Local access only
- `server_port: 8080` - Use different port
- `share: false` - No public link

### Logging Configuration

```yaml
logging:
  level: "INFO"              # Log level: DEBUG, INFO, WARNING, ERROR
  file: "eopf_mcp.log"      # Log file path
```

## Environment Variables: .env

```bash
# Claude API (required if llm_provider: "claude")
ANTHROPIC_API_KEY=sk-ant-...

# CDSE S3 Credentials (required for Zarr downloads)
ACCESS_KEY_ID=your-key
SECRET_ACCESS_KEY=your-secret
```

## Configuration Examples

### Example 1: Production with Claude

```yaml
llm_provider: "claude"

claude:
  model: "claude-opus-4-6"
  max_tokens: 4096
  temperature: 0.7

gradio:
  server_name: "0.0.0.0"
  server_port: 7860
  share: true

logging:
  level: "INFO"
```

### Example 2: Local Development with Ollama

```yaml
llm_provider: "local"

local_llm:
  provider: "ollama"
  ollama:
    base_url: "http://localhost:11434"
    model: "llama3.1"
  max_tokens: 4096
  temperature: 0.7

gradio:
  server_name: "127.0.0.1"
  server_port: 7860
  share: false

logging:
  level: "DEBUG"
```

### Example 3: High-Performance Local

```yaml
llm_provider: "local"

local_llm:
  provider: "ollama"
  ollama:
    base_url: "http://localhost:11434"
    model: "qwen2.5:14b"        # Larger model
  max_tokens: 8192              # More tokens
  temperature: 0.5              # Less creative, more focused

gradio:
  server_name: "0.0.0.0"
  server_port: 7860
  share: false
```

## Switching Providers

To switch between Claude and local LLM:

1. Edit `config.yaml`:
   ```yaml
   llm_provider: "local"  # or "claude"
   ```

2. Restart Gradio:
   ```bash
   # Stop current server (Ctrl+C)
   uv run python gradio_app.py
   ```

**No code changes needed!**

## Configuration Priority

Settings are loaded in this order:

1. **config.yaml** - Main configuration
2. **.env** - Environment variables (API keys)
3. **Environment variables** - Override .env

Example:
```bash
# Override in shell
export GRADIO_PORT=8080
uv run python gradio_app.py
```

## Validation

Test your configuration:

```bash
# Check all settings
uv run python test_config.py

# Expected output:
# ✅ Configuration loaded
# ✅ LLM provider created
# ✅ Response: Hello from EOPF STAC MCP!
```

## Common Issues

### "Configuration file not found"
```
❌ Error: config.yaml not found
```
**Fix:** Create `config.yaml` from template above

### "ANTHROPIC_API_KEY not set"
```
❌ Error: ANTHROPIC_API_KEY not found
```
**Fix:** Add to `.env` file or switch to `llm_provider: "local"`

### "Connection refused" (Ollama)
```
❌ Error: Connection refused on localhost:11434
```
**Fix:** Start Ollama server: `ollama serve`

### "Model not found" (Ollama)
```
❌ Error: model 'llama3.1' not found
```
**Fix:** Download model: `ollama pull llama3.1`

## Performance Tuning

### For Speed
```yaml
claude:
  model: "claude-sonnet-4-5"  # Faster than Opus

# Or
local_llm:
  ollama:
    model: "llama3.2"  # Smaller model
```

### For Quality
```yaml
claude:
  model: "claude-opus-4-6"
  temperature: 0.3  # More focused

# Or
local_llm:
  ollama:
    model: "qwen2.5:14b"  # Larger model
  temperature: 0.3
```

### For Cost Savings
```yaml
llm_provider: "local"  # Free!

# Or use cheaper Claude model
claude:
  model: "claude-haiku-4"
```

## Advanced Usage

### Multiple Configurations

```bash
# Use different config file
python gradio_app.py --config prod_config.yaml
```

### Dynamic Configuration

```python
from config_loader import Config

config = Config("custom_config.yaml")
print(config.llm_provider)
```

## Security

- **Never commit `.env` file** - It contains secrets
- **.env is git-ignored** by default
- **Use `.env.example`** as template
- **Rotate API keys** periodically

## Support

- Configuration issues: Check `test_config.py` output
- LLM issues: See [LOCAL_LLM_SETUP.md](LOCAL_LLM_SETUP.md)
- General help: See [README.md](README.md)
