#!/usr/bin/env python3
"""
Chat client that uses Claude API with EOPF STAC MCP server.

This allows you to chat with Claude and have it query the STAC catalog
using natural language.
"""

import asyncio
import os
from typing import Any

from anthropic import AsyncAnthropic
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables from .env file
load_dotenv()


class STACChatClient:
    """Chat client that integrates Claude API with STAC MCP server."""

    def __init__(self, api_key: str | None = None):
        """Initialize the chat client.

        Args:
            api_key: Anthropic API key. If not provided, will use ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.anthropic = AsyncAnthropic(api_key=self.api_key)
        self.conversation_history = []

    async def run_chat(self):
        """Run the interactive chat session."""

        # Create server parameters for MCP server
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "main.py"],
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize MCP connection
                await session.initialize()

                # Get available tools from MCP server
                tools_response = await session.list_tools()

                # Convert MCP tools to Anthropic tool format
                tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                    for tool in tools_response.tools
                ]

                print("="*60)
                print("EOPF STAC Chat Client")
                print("="*60)
                print("Connected to STAC catalog: https://stac.core.eopf.eodc.eu")
                print(f"Available tools: {', '.join(t['name'] for t in tools)}")
                print("\nYou can ask questions like:")
                print("  - What collections are available?")
                print("  - Search for Sentinel-2 L1C products over [11.2, 45.5, 11.3, 45.6]")
                print("  - Show me Sentinel-3 OLCI collections")
                print("\nType 'quit' or 'exit' to end the conversation.")
                print("="*60 + "\n")

                # Chat loop
                while True:
                    # Get user input
                    user_message = input("You: ").strip()

                    if user_message.lower() in ["quit", "exit", "bye"]:
                        print("Goodbye!")
                        break

                    if not user_message:
                        continue

                    # Add user message to history
                    self.conversation_history.append({
                        "role": "user",
                        "content": user_message,
                    })

                    # Call Claude API with tools
                    response = await self._process_message(session, tools)

                    # Print Claude's response
                    print(f"\nClaude: {response}\n")

    async def _process_message(
        self,
        session: ClientSession,
        tools: list[dict[str, Any]]
    ) -> str:
        """Process a message through Claude API with tool use.

        Args:
            session: MCP session for calling tools
            tools: Available tools from MCP server

        Returns:
            Claude's final response
        """
        messages = self.conversation_history.copy()

        # Keep calling Claude until no more tool uses
        while True:
            response = await self.anthropic.messages.create(
                model="claude-opus-4-6",
                max_tokens=4096,
                tools=tools,
                messages=messages,
            )

            # Check if Claude wants to use tools
            tool_uses = [block for block in response.content if block.type == "tool_use"]

            if not tool_uses:
                # No more tools to use, get final text response
                text_content = [block.text for block in response.content if hasattr(block, "text")]
                final_response = "\n".join(text_content)

                # Add assistant response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.content,
                })

                return final_response

            # Claude wants to use tools
            # Add Claude's response (with tool uses) to messages
            messages.append({
                "role": "assistant",
                "content": response.content,
            })

            # Execute each tool call
            tool_results = []
            for tool_use in tool_uses:
                print(f"  [Calling tool: {tool_use.name}]")

                # Call the MCP tool
                result = await session.call_tool(tool_use.name, tool_use.input)

                # Add tool result
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result.content[0].text,
                })

            # Add tool results to messages for next iteration
            messages.append({
                "role": "user",
                "content": tool_results,
            })

            # Update conversation history with tool use and results
            self.conversation_history.append({
                "role": "assistant",
                "content": response.content,
            })
            self.conversation_history.append({
                "role": "user",
                "content": tool_results,
            })


async def main():
    """Run the chat client."""
    try:
        client = STACChatClient()
        await client.run_chat()
    except ValueError as e:
        print(f"Error: {e}")
        print("\nTo use this chat client, you need an Anthropic API key.")
        print("Get one at: https://console.anthropic.com/")
        print("\nThen set it as an environment variable:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        print("\nOr create a .env file with:")
        print("  ANTHROPIC_API_KEY=your-api-key-here")


if __name__ == "__main__":
    asyncio.run(main())
