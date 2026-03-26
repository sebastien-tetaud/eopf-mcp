"""Chat handler - reuses existing MCP and LLM logic."""

import asyncio
from typing import AsyncGenerator, Any
from datetime import datetime
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from eopf_mcp.llm.provider import create_llm_provider
from eopf_mcp.api.models import Message, StreamEvent
from eopf_mcp.llm.config import get_config


class ChatHandler:
    """Handles chat logic with MCP and LLM."""

    def __init__(self):
        self.config = get_config()
        self.llm = create_llm_provider()
        self.mcp_session: ClientSession | None = None
        self.mcp_tools: list[dict] | None = None
        self._initialization_lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize MCP connection."""
        async with self._initialization_lock:
            if self._initialized:
                return

            # Determine correct path to mcp_server.py
            current_dir = Path.cwd()
            if (current_dir / "src" / "eopf_mcp" / "mcp_server.py").exists():
                # Running from project root
                mcp_server_path = "src/eopf_mcp/mcp_server.py"
            elif (current_dir / "eopf_mcp" / "mcp_server.py").exists():
                # Running from src/ directory
                mcp_server_path = "eopf_mcp/mcp_server.py"
            else:
                raise FileNotFoundError("Cannot find mcp_server.py - must run from project root or src/ directory")

            server_params = StdioServerParameters(
                command="uv",
                args=["run", "python", mcp_server_path],
            )

            # Start MCP server as background task
            self._mcp_connection_task = asyncio.create_task(
                self._run_mcp_server(server_params)
            )

            # Wait for initialization
            for _ in range(40):  # 20 seconds max
                if self.mcp_session and self.mcp_tools:
                    self._initialized = True
                    print(f"✓ MCP initialized with {len(self.mcp_tools)} tools")
                    return
                await asyncio.sleep(0.5)

            raise RuntimeError("Failed to initialize MCP session")

    async def _run_mcp_server(self, server_params: StdioServerParameters) -> None:
        """Run MCP server and keep connection alive."""
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

                # Keep session alive
                await asyncio.Event().wait()

    async def process_message(
        self,
        message: str,
        history: list[Message]
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Process a user message and stream response events.

        Yields StreamEvent objects:
        - message_start: Beginning of response
        - content_delta: Incremental text content
        - tool_call: Tool is being called
        - tool_result: Tool execution result
        - message_end: Response complete
        - error: Error occurred
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Build message list for LLM
            messages = []
            for msg in history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

            messages.append({"role": "user", "content": message})

            yield StreamEvent(
                event="message_start",
                data={"timestamp": datetime.now().isoformat()}
            )

            tool_calls_made = []

            # Agentic loop - continue until no more tools
            while True:
                # Call LLM
                response = await self.llm.create_message(
                    messages=messages,
                    tools=self.mcp_tools,
                )

                # Extract tool uses and text
                tool_uses, text_response = self.llm.format_tool_response(response)

                if not tool_uses:
                    # No more tools - stream final response
                    yield StreamEvent(
                        event="content_delta",
                        data={"text": text_response}
                    )

                    yield StreamEvent(
                        event="message_end",
                        data={
                            "timestamp": datetime.now().isoformat(),
                            "tools_used": tool_calls_made
                        }
                    )
                    return

                # Add assistant message to context
                if hasattr(response, 'content'):
                    messages.append({"role": "assistant", "content": response.content})
                else:
                    messages.append({"role": "assistant", "content": text_response})

                # Execute tools
                tool_results = []
                for tool_use in tool_uses:
                    tool_calls_made.append(tool_use.name)

                    yield StreamEvent(
                        event="tool_call",
                        data={
                            "name": tool_use.name,
                            "input": tool_use.input
                        }
                    )

                    # Call MCP tool
                    result = await self.mcp_session.call_tool(
                        tool_use.name,
                        tool_use.input
                    )

                    result_text = result.content[0].text

                    yield StreamEvent(
                        event="tool_result",
                        data={
                            "name": tool_use.name,
                            "result": result_text
                        }
                    )

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": result_text,
                    })

                # Add tool results to context
                messages.append({"role": "user", "content": tool_results})

        except Exception as e:
            yield StreamEvent(
                event="error",
                data={"message": str(e)}
            )


# Global chat handler instance
_chat_handler: ChatHandler | None = None


async def get_chat_handler() -> ChatHandler:
    """Get or create global chat handler."""
    global _chat_handler

    if _chat_handler is None:
        _chat_handler = ChatHandler()
        await _chat_handler.initialize()

    return _chat_handler
