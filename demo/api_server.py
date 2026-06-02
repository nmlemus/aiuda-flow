"""
Demo: aiuda-flow as a FastAPI server
======================================
Runs the same research pipeline but exposed as HTTP API.

    python demo/api_server.py

Endpoints:
    GET  /           → health + node list
    POST /run        → sync execution
    POST /stream     → SSE streaming
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from typing import Any
from typing_extensions import TypedDict, Annotated
import operator

from aiuda_flow import Graph, Node
from aiuda_flow.adapters.api import create_app
from langchain_anthropic import ChatAnthropic
import uvicorn

llm = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=512)


class SimpleState(TypedDict, total=False):
    query: str
    result: str
    messages: Annotated[list[Any], operator.add]
    metadata: dict[str, Any]


class AnswerNode(Node):
    """Answers a query directly."""

    def run(self, state: SimpleState) -> dict:
        query = state.get("query", "Hello!")
        response = llm.invoke(f"Answer briefly: {query}")
        return {"result": response.content.strip()}


graph = Graph(state_schema=SimpleState).add(AnswerNode(), entry=True)
app = create_app(graph, title="aiuda-flow demo")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 API server at http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
