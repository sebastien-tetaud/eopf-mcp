# OVH AI Endpoints Setup Guide

This guide explains how to use OVH AI Endpoints with the EOPF STAC MCP server.

## What is OVH AI Endpoints?

OVH AI Endpoints provides OpenAI-compatible API access to various AI models hosted on OVH Cloud infrastructure. Benefits include:

- **European hosting** - Data stays in Europe (GDPR compliant)
- **Pay-as-you-go** - No subscription, pay per request
- **Multiple models** - Access to various open-source models
- **OpenAI compatible** - Standard API format

## Setup Steps

### 1. Get OVH AI Endpoints Access

1. Sign up at: https://endpoints.ai.cloud.ovh.net/
2. Create an API token
3. Note your token (starts with `eyJ...`)

### 2. Configure EOPF MCP

Edit `config.yaml`:

```yaml
# Set provider to OVH
llm_provider: "ovh"

ovh:
  base_url: "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1"
  model: "Qwen3Guard-Gen-8B"  # or other available model
  max_tokens: 4096
  temperature: 0.7
```

### 3. Add API Token

Edit `.env`:

```bash
OVH_AI_ENDPOINTS_ACCESS_TOKEN=your-token-here
```

### 4. Run Gradio App

```bash
uv run python gradio_app.py
```

You should see:
```
🚀 Initializing STAC Gradio App...
📝 LLM Provider: ovh
🤖 Using OVH AI Endpoints: Qwen3Guard-Gen-8B
```

## Available Models

OVH AI Endpoints offers various models. Check https://endpoints.ai.cloud.ovh.net/ for current list.

**Recommended for STAC queries:**
- `Llama-3.1-8B-Instruct` - **Recommended** - Good instruction following and tool use
- `Mistral-7B-Instruct-v0.3` - Fast responses, alternative option
- ~~`Qwen3Guard-Gen-8B`~~ - Safety/moderation model, not for general chat

Update `config.yaml` to change models:

```yaml
ovh:
  model: "Llama-3.1-8B-Instruct"
```

## Configuration Options

### Basic Configuration

```yaml
ovh:
  base_url: "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1"
  model: "Qwen3Guard-Gen-8B"
  max_tokens: 4096          # Response length
  temperature: 0.7          # Creativity (0.0-1.0)
```

### For Better Quality

```yaml
ovh:
  model: "Qwen3Guard-Gen-8B"
  max_tokens: 8192          # Longer responses
  temperature: 0.3          # More focused
```

### For Faster Responses

```yaml
ovh:
  model: "Mistral-7B-Instruct-v0.3"  # Smaller model
  max_tokens: 2048                    # Shorter responses
  temperature: 0.5
```

## Testing

Test your OVH configuration:

```bash
# Test configuration
uv run python test_config.py

# Expected output:
# ✅ LLM provider created: OVHProvider
# ✅ Response: Hello from EOPF STAC MCP!
```

## Example Usage

Once configured, use the Gradio app normally:

```
You: What collections are available?
Claude (OVH): [Lists STAC collections using the list_collections tool]

You: Search for Sentinel-2 data over Italy
Claude (OVH): [Searches and returns results]
```

## Pricing

OVH AI Endpoints uses pay-as-you-go pricing:
- Charged per 1M tokens
- Pricing varies by model
- Check current rates at: https://endpoints.ai.cloud.ovh.net/pricing

**Estimated costs for STAC queries:**
- Simple query (list collections): ~$0.001
- Complex search with tool use: ~$0.005
- Typical session (10 queries): ~$0.03

Much cheaper than Claude API for high-volume usage!

## Troubleshooting

### Token Not Working

```
❌ Error: OVH_AI_ENDPOINTS_ACCESS_TOKEN not found
```

**Fix:** Add token to `.env` file
```bash
OVH_AI_ENDPOINTS_ACCESS_TOKEN=your-token-here
```

### Connection Refused

```
❌ Error: Connection refused
```

**Fix:** Check internet connection and OVH status

### Model Not Found

```
❌ Error: Model not found
```

**Fix:** Update model name in `config.yaml` with available model

### Tool Use Not Reliable

OVH models may not always use tools correctly. Try:

1. **Use explicit instructions**
   ```
   "Use the list_collections tool to show me all collections"
   ```

2. **Try different model**
   ```yaml
   ovh:
     model: "Llama-3.1-8B-Instruct"  # Better instruction following
   ```

3. **Fall back to Claude if needed**
   ```yaml
   llm_provider: "claude"
   ```

## Comparison: Claude vs OVH vs Ollama

| Feature | Claude API | OVH AI Endpoints | Ollama (Local) |
|---------|-----------|------------------|----------------|
| **Cost** | $$$ | $ | Free |
| **Quality** | Excellent | Good | Good |
| **Speed** | Fast | Fast | Medium (CPU) |
| **Tool Use** | Excellent | Good | Fair |
| **Privacy** | Cloud (US) | Cloud (EU) | Local |
| **Setup** | API key | API token | Install + download |
| **Offline** | No | No | Yes |

**When to use OVH:**
- ✅ Need quality better than local LLM
- ✅ Want to avoid US cloud services (GDPR)
- ✅ Have budget constraints vs Claude
- ✅ Don't want to manage local infrastructure

**When NOT to use OVH:**
- ❌ Need best possible quality (use Claude)
- ❌ Want completely free (use Ollama)
- ❌ Need offline operation (use Ollama)

## Advanced: Custom Models

If you have access to custom models on OVH:

```yaml
ovh:
  base_url: "https://your-custom-endpoint.ovh.net/v1"
  model: "your-custom-model"
  max_tokens: 4096
```

## API Reference

OVH AI Endpoints uses OpenAI-compatible API:

```python
import requests

url = "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
payload = {
    "model": "Qwen3Guard-Gen-8B",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 512
}

response = requests.post(url, json=payload, headers=headers)
```

## Support

- OVH Documentation: https://help.ovhcloud.com/
- OVH Community: https://community.ovh.com/
- API Status: https://status.ovhcloud.com/

## Switching Providers

To switch from OVH to another provider:

**To Claude:**
```yaml
llm_provider: "claude"
```

**To Ollama:**
```yaml
llm_provider: "local"
```

Then restart the Gradio app. No code changes needed!

## Security Notes

- **Never commit tokens** - Keep `.env` file git-ignored
- **Rotate tokens regularly** - Generate new tokens periodically
- **Monitor usage** - Check OVH dashboard for billing
- **Use HTTPS** - All requests encrypted in transit

## Getting Help

If OVH isn't working well:
1. Check OVH status page
2. Verify token in `.env` file
3. Try different model
4. Check OVH community forums
5. Fall back to Claude or Ollama if needed
