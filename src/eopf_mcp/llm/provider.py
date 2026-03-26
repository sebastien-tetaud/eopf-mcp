#!/usr/bin/env python3
"""
LLM provider abstraction layer.
Supports Claude API and local LLMs (Ollama, LlamaCpp, vLLM).
"""

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List

import requests
from anthropic import AsyncAnthropic

from eopf_mcp.llm.config import get_config


def remove_think_tags(text: str) -> str:
    """
    Remove <think>...</think> tags and their content from text.

    Args:
        text: Input text that may contain <think> tags

    Returns:
        Text with <think> tags and their content removed
    """
    # Remove <think>...</think> blocks (including multiline)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Clean up any extra whitespace left behind
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Multiple blank lines -> double newline
    return text.strip()


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def create_message(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] | None = None,
    ) -> Any:
        """
        Create a message with the LLM.

        Args:
            messages: List of message dicts with role and content
            tools: Optional list of tools (MCP tools)

        Returns:
            LLM response
        """
        pass

    @abstractmethod
    def format_tool_response(self, response: Any) -> tuple[List[Any], str]:
        """
        Format LLM response to extract tool uses and text.

        Args:
            response: Raw LLM response

        Returns:
            Tuple of (tool_uses, text_response)
        """
        pass


class ClaudeProvider(LLMProvider):
    """Claude API provider."""

    def __init__(self, api_key: str):
        """Initialize Claude provider."""
        self.client = AsyncAnthropic(api_key=api_key)
        self.config = get_config()

    async def create_message(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] | None = None,
    ) -> Any:
        """Create message with Claude API."""
        kwargs = {
            "model": self.config.claude_model,
            "max_tokens": self.config.claude_max_tokens,
            "messages": messages,
        }

        if tools:
            kwargs["tools"] = tools

        return await self.client.messages.create(**kwargs)

    def format_tool_response(self, response: Any) -> tuple[List[Any], str]:
        """Extract tool uses and text from Claude response."""
        tool_uses = [block for block in response.content if block.type == "tool_use"]
        text_blocks = [block.text for block in response.content if hasattr(block, "text")]
        text_response = "\n".join(text_blocks)

        # Remove <think> tags from the response
        text_response = remove_think_tags(text_response)

        return tool_uses, text_response


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    def __init__(self):
        """Initialize Ollama provider."""
        self.config = get_config()
        self.base_url = self.config.ollama_base_url
        self.model = self.config.ollama_model

    async def create_message(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] | None = None,
    ) -> Any:
        """Create message with Ollama."""
        # Convert messages to Ollama format
        prompt = self._format_prompt(messages, tools)

        # Call Ollama API
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.local_llm_temperature,
                "num_predict": self.config.local_llm_max_tokens,
            }
        }

        # Synchronous request (will run in event loop via run_in_executor)
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()
        return OllamaResponse(result, tools)

    def _format_prompt(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] | None) -> str:
        """Format messages and tools into a prompt for Ollama."""
        prompt_parts = []

        # Add tool definitions if available
        if tools:
            prompt_parts.append("You have access to the following tools:\n")
            for tool in tools:
                prompt_parts.append(f"- {tool['name']}: {tool['description']}")
                prompt_parts.append(f"  Input schema: {json.dumps(tool['input_schema'])}\n")

            prompt_parts.append("\nTo use a tool, respond with JSON in this format:")
            prompt_parts.append('{"tool_use": {"name": "tool_name", "input": {...}}}')
            prompt_parts.append("\nOtherwise, respond with normal text.\n")

        # Add conversation history
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if isinstance(content, str):
                prompt_parts.append(f"\n{role.upper()}: {content}")
            elif isinstance(content, list):
                # Handle tool results
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        prompt_parts.append(f"\nTOOL RESULT: {item.get('content', '')}")

        return "\n".join(prompt_parts)

    def format_tool_response(self, response: Any) -> tuple[List[Any], str]:
        """Extract tool uses and text from Ollama response."""
        # Remove <think> tags from the response text
        text_response = remove_think_tags(response.text)
        return response.tool_uses, text_response


class OllamaResponse:
    """Wrapper for Ollama response to match Claude API format."""

    def __init__(self, raw_response: Dict[str, Any], tools: List[Dict[str, Any]] | None):
        """Initialize Ollama response wrapper."""
        self.raw_response = raw_response
        self.text = raw_response.get("response", "")
        self.tool_uses = []

        # Try to parse tool use from response
        if tools:
            self._parse_tool_use()

    def _parse_tool_use(self):
        """Parse tool use from response text."""
        try:
            # Look for JSON in response
            if "tool_use" in self.text:
                # Try to extract JSON
                start = self.text.find("{")
                end = self.text.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = self.text[start:end]
                    parsed = json.loads(json_str)

                    if "tool_use" in parsed:
                        tool_data = parsed["tool_use"]
                        # Create a tool use object similar to Claude's format
                        tool_use = ToolUse(
                            id=f"tool_{len(self.tool_uses)}",
                            name=tool_data.get("name"),
                            input=tool_data.get("input", {})
                        )
                        self.tool_uses.append(tool_use)

                        # Remove tool JSON from text
                        self.text = self.text[:start] + self.text[end:]
        except json.JSONDecodeError:
            pass  # Not a tool use, just regular text


class ToolUse:
    """Tool use object to match Claude API format."""

    def __init__(self, id: str, name: str, input: Dict[str, Any]):
        """Initialize tool use."""
        self.type = "tool_use"
        self.id = id
        self.name = name
        self.input = input


class OVHProvider(LLMProvider):
    """OVH AI Endpoints provider."""

    def __init__(self, api_token: str):
        """Initialize OVH provider."""
        self.config = get_config()
        self.base_url = self.config.ovh_base_url
        self.model = self.config.ovh_model
        self.api_token = api_token

    async def create_message(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] | None = None,
    ) -> Any:
        """Create message with OVH AI Endpoints."""
        # Format messages for OpenAI-compatible API
        formatted_messages = self._format_messages(messages, tools)

        # Call OVH API
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": self.config.ovh_max_tokens,
            "temperature": self.config.ovh_temperature,
        }

        # Synchronous request (will run in event loop via run_in_executor)
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()

        result = response.json()
        return OVHResponse(result, tools)

    def _format_messages(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] | None
    ) -> List[Dict[str, str]]:
        """Format messages for OVH API (OpenAI-compatible format)."""
        formatted = []

        # Add system message with tool instructions if tools are available
        if tools:
            tool_descriptions = []
            for tool in tools:
                tool_descriptions.append(
                    f"- {tool['name']}: {tool['description']}\n"
                    f"  Input: {json.dumps(tool['input_schema'])}"
                )

            system_message = {
                "role": "system",
                "content": (
                    "You are a helpful assistant with access to tools. "
                    "Available tools:\n" + "\n".join(tool_descriptions) +
                    "\n\nTo use a tool, respond with JSON: "
                    '{"tool_use": {"name": "tool_name", "input": {...}}}'
                )
            }
            formatted.append(system_message)

        # Convert messages
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if isinstance(content, str):
                formatted.append({"role": role, "content": content})
            elif isinstance(content, list):
                # Handle tool results
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        formatted.append({
                            "role": "user",
                            "content": f"Tool result: {item.get('content', '')}"
                        })

        return formatted

    def format_tool_response(self, response: Any) -> tuple[List[Any], str]:
        """Extract tool uses and text from OVH response."""
        # Remove <think> tags from the response text
        text_response = remove_think_tags(response.text)
        return response.tool_uses, text_response


class OVHResponse:
    """Wrapper for OVH response to match Claude API format."""

    def __init__(self, raw_response: Dict[str, Any], tools: List[Dict[str, Any]] | None):
        """Initialize OVH response wrapper."""
        self.raw_response = raw_response
        self.text = ""
        self.tool_uses = []

        # Extract message content
        if "choices" in raw_response and len(raw_response["choices"]) > 0:
            self.text = raw_response["choices"][0]["message"]["content"]

        # Try to parse tool use from response
        if tools:
            self._parse_tool_use()

    def _parse_tool_use(self):
        """Parse tool use from response text."""
        try:
            # Look for JSON in response
            if "tool_use" in self.text:
                # Try to extract JSON
                start = self.text.find("{")
                end = self.text.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = self.text[start:end]
                    parsed = json.loads(json_str)

                    if "tool_use" in parsed:
                        tool_data = parsed["tool_use"]
                        # Create a tool use object similar to Claude's format
                        tool_use = ToolUse(
                            id=f"tool_{len(self.tool_uses)}",
                            name=tool_data.get("name"),
                            input=tool_data.get("input", {})
                        )
                        self.tool_uses.append(tool_use)

                        # Remove tool JSON from text
                        self.text = self.text[:start] + self.text[end:]
                        self.text = self.text.strip()
        except json.JSONDecodeError:
            pass  # Not a tool use, just regular text


def create_llm_provider() -> LLMProvider:
    """
    Create LLM provider based on configuration.

    Returns:
        LLM provider instance
    """
    config = get_config()

    if config.llm_provider == "claude":
        api_key = config.anthropic_api_key
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        return ClaudeProvider(api_key)

    elif config.llm_provider == "ovh":
        api_token = config.ovh_api_token
        if not api_token:
            raise ValueError("OVH_AI_ENDPOINTS_ACCESS_TOKEN not found in environment")
        return OVHProvider(api_token)

    elif config.llm_provider == "local":
        local_provider = config.local_llm_provider

        if local_provider == "ollama":
            return OllamaProvider()
        else:
            raise ValueError(f"Unsupported local LLM provider: {local_provider}")

    else:
        raise ValueError(f"Unsupported LLM provider: {config.llm_provider}")
