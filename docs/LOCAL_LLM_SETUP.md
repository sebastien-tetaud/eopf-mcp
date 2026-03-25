# Local LLM Setup Guide

This guide explains how to use local LLMs (Ollama) instead of Claude API with the EOPF STAC MCP server.

## Why Use Local LLM?

- **No API costs** - Run completely free
- **Privacy** - Data stays on your machine
- **Offline** - Works without internet (after model download)
- **Customization** - Use any model you want

## Option 1: Ollama (Recommended)

### Install Ollama

**macOS/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Or download from:** https://ollama.com/download

### Download a Model

```bash
# Recommended: Llama 3.1 8B (good balance of speed/quality)
ollama pull llama3.1

# Or other options:
ollama pull llama3.2       # Smaller, faster
ollama pull qwen2.5:14b    # Larger, more capable
ollama pull mistral        # Alternative model
```

### Start Ollama Server

```bash
ollama serve
```

This starts Ollama on `http://localhost:11434`

### Configure EOPF MCP

Edit `config.yaml`:

```yaml
# Change provider to local
llm_provider: "local"

local_llm:
  provider: "ollama"
  ollama:
    base_url: "http://localhost:11434"
    model: "llama3.1"  # or your chosen model
```

### Run Gradio App

```bash
uv run python gradio_app.py
```

You should see:
```
🚀 Initializing STAC Gradio App...
📝 LLM Provider: local
🤖 Using local LLM: ollama (llama3.1)
```

## Option 2: LlamaCpp (Advanced)

### Install LlamaCpp

```bash
pip install llama-cpp-python
```

### Download a GGUF Model

Download from HuggingFace, for example:
```bash
# Example: Llama 3.1 8B GGUF
wget https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
```

### Configure

Edit `config.yaml`:

```yaml
llm_provider: "local"

local_llm:
  provider: "llamacpp"
  llamacpp:
    model_path: "/path/to/your/model.gguf"
    n_ctx: 4096
    n_gpu_layers: 35  # Use GPU acceleration
```

**Note:** LlamaCpp provider implementation coming soon!

## Comparing Providers

| Provider | Pros | Cons |
|----------|------|------|
| **Claude API** | - Best quality<br>- Tool use optimized<br>- Fast | - Costs money<br>- Requires internet<br>- API key needed |
| **Ollama** | - Free<br>- Easy setup<br>- Good quality | - Slower on CPU<br>- Needs RAM (8GB+)<br>- Tool use less reliable |
| **LlamaCpp** | - Very customizable<br>- GPU acceleration<br>- Free | - Complex setup<br>- Manual model management |

## Model Recommendations

### For STAC Catalog Queries

| Model | Size | RAM Needed | Quality | Speed |
|-------|------|------------|---------|-------|
| **llama3.2** | 3B | 4GB | Good | Very Fast |
| **llama3.1** | 8B | 8GB | Very Good | Fast |
| **qwen2.5:14b** | 14B | 16GB | Excellent | Medium |
| **llama3.1:70b** | 70B | 64GB+ | Best | Slow |

**Recommended:** Start with `llama3.1` (8B) - good balance of quality and speed.

## Testing Local LLM

### 1. Test Ollama Directly

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1",
  "prompt": "What is STAC?",
  "stream": false
}'
```

### 2. Test with Gradio

Start the app and ask:
```
What collections are available?
```

The local LLM should call the `list_collections` tool.

## Troubleshooting

### Ollama Not Found

```
❌ Error: Connection refused
```

**Fix:** Start Ollama server
```bash
ollama serve
```

### Model Not Downloaded

```
❌ Error: model not found
```

**Fix:** Pull the model
```bash
ollama pull llama3.1
```

### Tool Use Not Working

Local LLMs may not reliably use tools. Try:

1. **Use a larger model** - Better instruction following
   ```bash
   ollama pull qwen2.5:14b
   ```

2. **Simplify your query** - Be more explicit
   ```
   # Instead of: "Show me data"
   # Try: "List all collections using the list_collections tool"
   ```

3. **Switch to Claude** - Edit `config.yaml`:
   ```yaml
   llm_provider: "claude"
   ```

### Slow Performance

**CPU Mode:**
- Use smaller models (llama3.2)
- Reduce context length in config
- Be patient - first query warms up model

**GPU Acceleration:**
```bash
# Install with GPU support
CMAKE_ARGS="-DLLAMA_CUDA=on" pip install llama-cpp-python
```

## Switching Between Providers

Edit `config.yaml` and restart Gradio:

```yaml
# Use Claude
llm_provider: "claude"

# Use Ollama
llm_provider: "local"
```

No code changes needed!

## Advanced: Custom System Prompts

You can enhance local LLM tool use by editing `llm_provider.py`:

```python
def _format_prompt(self, messages, tools):
    # Add better instructions for tool use
    prompt_parts = [
        "You are a helpful assistant with access to STAC catalog tools.",
        "Always use tools when the user asks about satellite data.",
        ...
    ]
```

## Performance Tips

1. **First query is slow** - Model loads into memory
2. **Use keep-alive** - Ollama keeps model in memory for 5 minutes
3. **Batch queries** - Ask multiple questions in one session
4. **GPU helps a lot** - Consider CUDA/Metal acceleration

## Resources

- Ollama: https://ollama.com
- Available models: https://ollama.com/library
- LlamaCpp: https://github.com/ggerganov/llama.cpp
- GGUF models: https://huggingface.co/models?search=gguf

## Getting Help

If local LLM isn't working well:
1. Check Ollama logs: `ollama logs`
2. Try different model: `ollama pull qwen2.5`
3. Fall back to Claude: Edit `config.yaml`
4. Report issues: GitHub repository
