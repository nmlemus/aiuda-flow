"""
FastAPI adapter — exposes the graph as an HTTP API.
Supports both sync /run and streaming /stream (SSE).

Usage:
    from aiuda_flow.adapters.api import create_app
    app = create_app(graph)
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
import json
from typing import Any
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..core.graph import Graph


class RunRequest(BaseModel):
    state: dict[str, Any] = {}


def create_app(graph: Graph, title: str = "aiuda-flow") -> FastAPI:
    app = FastAPI(title=title)

    @app.get("/")
    def health():
        return {"status": "ok", "nodes": [n.name for n in graph._nodes]}

    @app.post("/run")
    def run(req: RunRequest):
        result = graph.run(req.state or None)
        return {"result": result}

    @app.post("/stream")
    def stream(req: RunRequest):
        def event_generator():
            for step_output in graph.stream(req.state or None):
                # LangGraph stream yields (node_name, state_update) tuples
                if isinstance(step_output, tuple):
                    node, update = step_output
                    data = json.dumps({"node": node, "update": update}, default=str)
                else:
                    data = json.dumps({"update": step_output}, default=str)
                yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    return app
