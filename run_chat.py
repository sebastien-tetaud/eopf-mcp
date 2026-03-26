#!/usr/bin/env python3
"""Entry point for chat client."""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from eopf_mcp.chat.client import main

if __name__ == "__main__":
    asyncio.run(main())
