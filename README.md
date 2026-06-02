# aiuda-flow

Portable GenAI workflow orchestration — **LangGraph + Arize Phoenix**.

Build observable, composable AI pipelines that run anywhere:
- VS Code / local terminal
- Claude Code, GitHub Copilot, any MCP-enabled agent harness
- Coder cloud infrastructure
- Custom UIs via SSE/WebSocket

---

## Quick Start

```bash
pip install aiuda-flow
cp .env.example .env  # add your ANTHROPIC_API_KEY
python demo/research_pipeline.py "What is LangGraph?"
```

## Architecture

```
aiuda-flow
├── core/       LangGraph wrapper — nodes, graph, state
├── observe/    Arize Phoenix auto-instrumentation
└── adapters/
    ├── local   stdout streaming, VS Code
    ├── api     FastAPI HTTP + SSE
    └── mcp     MCP tool server (Claude Code / Copilot)
```

## Define a node

```python
from aiuda_flow import Graph, Node

class MyNode(Node):
    def run(self, state):
        # state in → state updates out
        return {"result": "done"}

graph = Graph().add(MyNode())
result = graph.run()
```

## Multi-node pipeline

```python
graph = (
    Graph(state_schema=MyState)
    .add(PlannerNode(), entry=True)
    .add(ResearcherNode())
    .add(SynthesizerNode())
)
result = graph.run({"query": "..."})
```

## Observability

```python
from aiuda_flow import setup_tracing

setup_tracing(project_name="my-project", local=True)
# → Opens Phoenix UI at http://localhost:6006
```

## Run as API

```python
from aiuda_flow.adapters.api import create_app
import uvicorn

app = create_app(graph)
uvicorn.run(app, port=8000)
# POST /run  → sync
# POST /stream → SSE
```

## Run as MCP server

```python
from aiuda_flow.adapters.mcp import create_mcp_server

server, stdio_server = create_mcp_server(graph)
# add to claude_desktop_config.json or .mcp.json
```

## Demo

```bash
# Research pipeline (3 nodes + Arize tracing)
python demo/research_pipeline.py "What is LangGraph?"

# FastAPI server
python demo/api_server.py
curl -X POST http://localhost:8000/run -H "Content-Type: application/json" \
  -d '{"state": {"query": "What is LangGraph?"}}'
```

## Environment Detection

| Signal | Adapter |
|---|---|
| `MCP_SERVER=true` | MCP stdio |
| `PORT` env var | FastAPI |
| `UI_BRIDGE=true` | SSE bridge |
| none | local stdout |

---

Built by [Aiuda Labs](https://aiudalabs.com)
