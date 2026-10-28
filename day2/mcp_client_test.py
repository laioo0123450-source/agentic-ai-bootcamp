
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

BASE_DIR = Path(__file__).resolve().parent

async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(BASE_DIR / "mcp_server.py")],
        cwd=str(BASE_DIR),
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            names = [tool.name for tool in tools.tools]
            print("TOOLS:", names)

            assert {"search_assets", "remember", "recall"} <= set(names)

            result = await session.call_tool(
                "search_assets",
                {"criticality": "High"}
            )
            assert not result.is_error
            print("SEARCH:", result.content[0].text[:300])

            result = await session.call_tool(
                "remember",
                {"key": "day2", "note": "custom MCP server works"}
            )
            assert not result.is_error

            result = await session.call_tool("recall", {"key": "day2"})
            assert not result.is_error
            print("MEMORY:", result.content[0].text)
            assert "custom MCP server works" in result.content[0].text

            resources = await session.list_resources()
            print("RESOURCES:", [str(r.uri) for r in resources.resources])

            prompts = await session.list_prompts()
            print("PROMPTS:", [p.name for p in prompts.prompts])

            print("LAB 2.2 BASIC CHECKS PASSED")

if __name__ == "__main__":
    asyncio.run(main())



