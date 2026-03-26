#!/usr/bin/env python3
"""
Configuration loader for EOPF STAC MCP.
"""

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration manager for the application."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration.

        Args:
            config_path: Path to YAML configuration file
        """
        # Try to find config.yaml in multiple locations
        if not Path(config_path).exists():
            # Get project root (4 levels up from this file: eopf_mcp/llm/config.py)
            project_root = Path(__file__).parent.parent.parent.parent

            # Try config/config.yaml (new location)
            config_dir = project_root / "config" / config_path
            if config_dir.exists():
                config_path = str(config_dir)
            # Try root/config.yaml (alternative)
            elif (project_root / config_path).exists():
                config_path = str(project_root / config_path)
            # Try src/config.yaml (old location, for backwards compatibility)
            elif (project_root / "src" / config_path).exists():
                config_path = str(project_root / "src" / config_path)

        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key: Configuration key (e.g., "claude.model")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    @property
    def llm_provider(self) -> str:
        """Get LLM provider (claude or local)."""
        return self.get('llm_provider', 'claude')

    @property
    def claude_model(self) -> str:
        """Get Claude model name."""
        return self.get('claude.model', 'claude-opus-4-6')

    @property
    def claude_max_tokens(self) -> int:
        """Get Claude max tokens."""
        return self.get('claude.max_tokens', 4096)

    @property
    def claude_temperature(self) -> float:
        """Get Claude temperature."""
        return self.get('claude.temperature', 0.7)

    @property
    def anthropic_api_key(self) -> str:
        """Get Anthropic API key from environment."""
        return os.getenv('ANTHROPIC_API_KEY', '')

    @property
    def ovh_base_url(self) -> str:
        """Get OVH base URL."""
        return self.get('ovh.base_url', 'https://oai.endpoints.kepler.ai.cloud.ovh.net/v1')

    @property
    def ovh_model(self) -> str:
        """Get OVH model name."""
        return self.get('ovh.model', 'Qwen3Guard-Gen-8B')

    @property
    def ovh_max_tokens(self) -> int:
        """Get OVH max tokens."""
        return self.get('ovh.max_tokens', 4096)

    @property
    def ovh_temperature(self) -> float:
        """Get OVH temperature."""
        return self.get('ovh.temperature', 0.7)

    @property
    def ovh_api_token(self) -> str:
        """Get OVH API token from environment."""
        return os.getenv('OVH_AI_ENDPOINTS_ACCESS_TOKEN', '')

    @property
    def local_llm_provider(self) -> str:
        """Get local LLM provider (ollama, llamacpp, vllm)."""
        return self.get('local_llm.provider', 'ollama')

    @property
    def ollama_base_url(self) -> str:
        """Get Ollama base URL."""
        return self.get('local_llm.ollama.base_url', 'http://localhost:11434')

    @property
    def ollama_model(self) -> str:
        """Get Ollama model name."""
        return self.get('local_llm.ollama.model', 'llama3.1')

    @property
    def local_llm_max_tokens(self) -> int:
        """Get local LLM max tokens."""
        return self.get('local_llm.max_tokens', 4096)

    @property
    def local_llm_temperature(self) -> float:
        """Get local LLM temperature."""
        return self.get('local_llm.temperature', 0.7)

    @property
    def stac_url(self) -> str:
        """Get STAC catalog URL."""
        return self.get('mcp.stac_url', 'https://stac.core.eopf.eodc.eu')

    @property
    def default_search_limit(self) -> int:
        """Get default search limit."""
        return self.get('mcp.default_search_limit', 10)

    @property
    def gradio_server_name(self) -> str:
        """Get Gradio server name."""
        return self.get('gradio.server_name', '0.0.0.0')

    @property
    def gradio_server_port(self) -> int:
        """Get Gradio server port."""
        return self.get('gradio.server_port', 7860)

    @property
    def gradio_share(self) -> bool:
        """Get Gradio share setting."""
        return self.get('gradio.share', True)

    @property
    def api_host(self) -> str:
        """Get API server host."""
        return self.get('api.host', '0.0.0.0')

    @property
    def api_port(self) -> int:
        """Get API server port."""
        return self.get('api.port', 8000)

    @property
    def api_cors_origins(self) -> list[str]:
        """Get API CORS allowed origins."""
        return self.get('api.cors_origins', ['http://localhost:5173'])

    @property
    def session_storage_dir(self) -> str:
        """Get session storage directory."""
        return self.get('api.session_storage_dir', '.sessions')

    @property
    def max_sessions_per_user(self) -> int:
        """Get maximum sessions per user."""
        return self.get('api.max_sessions_per_user', 50)

    def __repr__(self) -> str:
        """String representation."""
        return f"Config(provider={self.llm_provider}, model={self.claude_model if self.llm_provider == 'claude' else self.ollama_model})"


# Global config instance
_config: Config | None = None


def get_config(config_path: str = "config.yaml") -> Config:
    """
    Get global configuration instance.

    Args:
        config_path: Path to configuration file

    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config
