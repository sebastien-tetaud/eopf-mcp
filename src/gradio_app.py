#!/usr/bin/env python3
"""
Gradio web interface for EOPF STAC chat.

This provides a user-friendly web UI to chat with LLM (Claude or local) and query the STAC catalog.
"""

import asyncio
import logging
import os
import re
import threading

import gradio as gr
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from config_loader import get_config
from llm_provider import create_llm_provider, ClaudeProvider, OVHProvider, OllamaProvider

# Load environment variables
load_dotenv()

# Disable HTTP debug logging that could expose tokens
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def sanitize_error_message(error: Exception) -> str:
    """Remove potential secrets from error messages."""
    error_str = str(error)

    # Redact common secret patterns
    error_str = re.sub(r'sk-ant-[a-zA-Z0-9-]+', 'sk-ant-***REDACTED***', error_str)
    error_str = re.sub(r'Bearer [a-zA-Z0-9._-]+', 'Bearer ***REDACTED***', error_str)
    error_str = re.sub(r'api[_-]?key["\s:=]+[a-zA-Z0-9-]+', 'api_key=***REDACTED***', error_str, flags=re.IGNORECASE)
    error_str = re.sub(r'token["\s:=]+[a-zA-Z0-9._-]+', 'token=***REDACTED***', error_str, flags=re.IGNORECASE)
    error_str = re.sub(r'secret["\s:=]+[a-zA-Z0-9]+', 'secret=***REDACTED***', error_str, flags=re.IGNORECASE)

    return error_str


class STACGradioApp:
    """STAC chatbot Gradio application."""

    def __init__(self):
        """Initialize the app."""
        self.config = get_config()
        self.llm = create_llm_provider()
        self.mcp_session = None
        self.mcp_tools = None
        self.loop = None
        self.mcp_task = None

    def format_response(self, text: str) -> str:
        """Format response text to properly display code blocks."""
        import re

        # Check if response contains TOOL RESULT with code dictionary
        if "TOOL RESULT:" in text and ("'code':" in text or '"code":' in text):
            # Use regex to extract code string between quotes
            patterns = [
                r"'code':\s*'(.*?)'\s*}",  # Single quotes - match until }
                r'"code":\s*"(.*?)"\s*}',  # Double quotes - match until }
            ]

            for pattern in patterns:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    code = match.group(1)
                    # Unescape the code
                    code = code.replace("\\n", "\n")
                    code = code.replace("\\'", "'")
                    code = code.replace('\\"', '"')
                    code = code.replace("\\\\", "\\")
                    return f"Here's the code:\n\n```python\n{code}\n```"

        # Check for code in access_instructions format
        if "'with_python':" in text or '"with_python":' in text:
            patterns = [
                r"'with_python':\s*'(.*?)'\s*[,}]",
                r'"with_python":\s*"(.*?)"\s*[,}]',
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    code = match.group(1)
                    code = code.replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"')
                    return f"```python\n{code}\n```"

        return text

    def start_background_loop(self):
        """Start a background event loop for MCP."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def run_mcp_server(self):
        """Run MCP server and keep it alive."""
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "main.py"],
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                tools_response = await session.list_tools()
                self.mcp_tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                    for tool in tools_response.tools
                ]

                self.mcp_session = session
                print(f"MCP Connected! Tools: {', '.join(t['name'] for t in self.mcp_tools)}")

                # Keep session alive
                await asyncio.Event().wait()

    async def chat(self, message: str, history: list[list[str]]) -> str:
        """Process a chat message."""
        if self.mcp_session is None or self.mcp_tools is None:
            return "Error: MCP server not initialized."

        try:
            messages = []

            # Build conversation from history - handle different formats
            for entry in history:
                if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                    user_msg, assistant_msg = entry[0], entry[1]
                    messages.append({"role": "user", "content": user_msg})
                    if assistant_msg:
                        messages.append({"role": "assistant", "content": assistant_msg})
                elif isinstance(entry, (list, tuple)) and len(entry) == 1:
                    # Handle single-item entries
                    messages.append({"role": "user", "content": entry[0]})

            messages.append({"role": "user", "content": message})

            tool_call_info = []
            while True:
                # Call LLM (Claude or local)
                response = await self.llm.create_message(
                    messages=messages,
                    tools=self.mcp_tools,
                )

                # Extract tool uses and text from response
                tool_uses, text_response = self.llm.format_tool_response(response)

                if not tool_uses:
                    # No more tools to use, return final response
                    final_response = text_response

                    # Format the response to display code properly
                    final_response = self.format_response(final_response)

                    if tool_call_info:
                        final_response = f"🔧 *Tools used: {', '.join(tool_call_info)}*\n\n{final_response}"

                    return final_response

                # For Claude API, keep original content; for others, create simplified version
                if hasattr(response, 'content'):
                    messages.append({"role": "assistant", "content": response.content})
                else:
                    # For local LLMs, create a simplified message
                    messages.append({"role": "assistant", "content": text_response})

                tool_results = []
                for tool_use in tool_uses:
                    tool_call_info.append(tool_use.name)
                    result = await self.mcp_session.call_tool(tool_use.name, tool_use.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": result.content[0].text,
                    })

                messages.append({"role": "user", "content": tool_results})

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            # Sanitize error before printing to console
            safe_error = sanitize_error_message(e)
            safe_details = sanitize_error_message(Exception(error_details))
            print(f"Error in chat: {str(safe_details)}")
            return f"Error: {safe_error}\n\nPlease try rephrasing your question or starting a new chat."


# Global app instance
app_instance = None


def chat_wrapper(message: str, history: list[list[str]]) -> str:
    """Wrapper to run async chat in background loop."""
    if app_instance is None or app_instance.loop is None:
        return "Error: App not initialized"

    try:
        # Validate history format
        if history and not isinstance(history, list):
            print(f"Warning: Invalid history type: {type(history)}")
            history = []

        future = asyncio.run_coroutine_threadsafe(
            app_instance.chat(message, history),
            app_instance.loop
        )

        return future.result(timeout=120)
    except TimeoutError:
        return "Error: Request timed out. Please try again with a simpler query."
    except Exception as e:
        import traceback
        # Sanitize error before printing to console
        safe_error = sanitize_error_message(e)
        safe_traceback = sanitize_error_message(Exception(traceback.format_exc()))
        print(f"Error in chat_wrapper: {str(safe_traceback)}")
        return f"Error: {safe_error}\n\nIf this persists, try refreshing the page."


def main():
    """Run the Gradio app."""
    global app_instance

    # Load configuration
    config = get_config()
    print(f"Initializing STAC Gradio App...")
    print(f"LLM Provider: {config.llm_provider}")

    if config.llm_provider == "claude":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY not set!")
            print("Please create a .env file with your API key")
            return
        print(f"Using Claude model: {config.claude_model}")
    elif config.llm_provider == "ovh":
        api_token = os.getenv("OVH_AI_ENDPOINTS_ACCESS_TOKEN")
        if not api_token:
            print("Error: OVH_AI_ENDPOINTS_ACCESS_TOKEN not set!")
            print("Please create a .env file with your API token")
            return
        print(f"Using OVH AI Endpoints: {config.ovh_model}")
    else:
        print(f"Using local LLM: {config.local_llm_provider} ({config.ollama_model})")

    app_instance = STACGradioApp()

    # Start background event loop
    print("Starting background event loop...")
    loop_thread = threading.Thread(target=app_instance.start_background_loop, daemon=True)
    loop_thread.start()

    # Wait for loop to start
    import time
    time.sleep(0.5)

    # Start MCP server in background loop
    print("Connecting to MCP server...")
    app_instance.mcp_task = asyncio.run_coroutine_threadsafe(
        app_instance.run_mcp_server(),
        app_instance.loop
    )

    # Wait for MCP to initialize
    for i in range(20):  # Wait up to 10 seconds
        if app_instance.mcp_tools:
            break
        time.sleep(0.5)

    if not app_instance.mcp_tools:
        print("MCP server not ready yet, but continuing...")

    # Create Gradio interface
    examples = [
        ["What collections are available?"],
        ["Search for Sentinel-2 L1C products over bbox [11.2, 45.5, 11.3, 45.6] from 2024"],
        ["Get Zarr URLs for Sentinel-2 L1C over bbox [11.2, 45.5, 11.3, 45.6] from 2024"],
        ["How do I download the first Zarr file?"],
        ["Tell me about the Sentinel-3 OLCI Level-2 collection"],
    ]

    status = "Connected" if app_instance.mcp_tools else "Connecting..."

    # Get LLM info for display
    config = get_config()
    llm_info = f"{config.llm_provider.title()}"
    if config.llm_provider == "claude":
        llm_info += f" ({config.claude_model})"
    elif config.llm_provider == "ovh":
        llm_info += f" ({config.ovh_model})"
    else:
        llm_info += f" ({config.ollama_model})"

    demo = gr.ChatInterface(
        fn=chat_wrapper,
        title="🛰️ EOPF STAC Catalog Chat",
        description=f"Chat with {llm_info} to explore the EOPF STAC catalog.\n\n**Status:** {status}",
        examples=examples,
    )

    print("\n🚀 Launching Gradio interface...")
    print("📡 Open: http://localhost:7860\n")

    try:
        demo.launch(
            server_name=config.gradio_server_name,
            server_port=config.gradio_server_port,
            share=config.gradio_share,
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")


if __name__ == "__main__":
    main()
