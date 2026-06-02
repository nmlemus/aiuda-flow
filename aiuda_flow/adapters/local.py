"""Local adapter — runs inline, streams output to stdout."""
from typing import Any
from ..core.graph import Graph


def run_local(graph: Graph, initial_state: dict[str, Any] | None = None, stream: bool = False):
    if stream:
        print("▶ Streaming graph execution:\n")
        for step, output in graph.stream(initial_state):
            print(f"  [{step}] → {output}")
        print("\n✓ Done")
    else:
        result = graph.run(initial_state)
        return result
