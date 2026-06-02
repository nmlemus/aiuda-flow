"""
MCP adapter — exposes graph nodes as MCP tools.
Compatible with Claude Code, Copilot, and any MCP-enabled agent harness.

Usage:
    from aiuda_flow.adapters.mcp import create_mcp_server
    server = create_mcp_server(graph)
    server.run()
"""
import json
from typing import Any
from ..core.graph import Graph


def create_mcp_server(graph: Graph, name: str = "aiuda-flow"):
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        import mcp.types as types
    except ImportError:
        raise ImportError("Install 'mcp' package: pip install mcp")

    server = Server(name)

    @server.list_tools()
    async def list_tools():
        tools = []
        for node in graph._nodes:
            tools.append(
                types.Tool(
                    name=node.name,
                    description=node.__class__.__doc__ or f"Run {node.name} node",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "state": {
                                "type": "object",
                                "description": "Input state for this node",
                            }
                        },
                    },
                )
            )
        # also expose full graph run
        tools.append(
            types.Tool(
                name="run_graph",
                description="Run the full graph pipeline",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "state": {"type": "object", "description": "Initial state"}
                    },
                },
            )
        )
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]):
        state = arguments.get("state", {})

        if name == "run_graph":
            result = graph.run(state or None)
            return [types.TextContent(type="text", text=json.dumps(result, default=str))]

        # find the node and run it directly
        for node in graph._nodes:
            if node.name == name:
                result = node.run(state)
                return [types.TextContent(type="text", text=json.dumps(result, default=str))]

        return [types.TextContent(type="text", text=f"Node '{name}' not found")]

    return server, stdio_server
