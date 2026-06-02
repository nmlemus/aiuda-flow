import os
from pathlib import Path
from typing import Any, Optional, Type
from langgraph.graph import StateGraph, END
from .node import Node
from .state import BaseState


class Graph:
    """
    Portable LangGraph wrapper. Auto-detects the runtime environment
    and selects the appropriate adapter on .run().
    """

    def __init__(self, state_schema: Type = BaseState):
        self._schema = state_schema
        self._nodes: list[Node] = []
        self._edges: list[tuple[str, str]] = []
        self._entry: Optional[str] = None
        self._compiled = None

    def add(self, node: Node, entry: bool = False) -> "Graph":
        self._nodes.append(node)
        if entry or self._entry is None:
            self._entry = node.name
        return self

    def edge(self, source: str, target: str) -> "Graph":
        self._edges.append((source, target))
        return self

    def _build(self):
        if self._compiled:
            return self._compiled

        builder = StateGraph(self._schema)
        for node in self._nodes:
            builder.add_node(node.name, node)

        builder.set_entry_point(self._entry)

        # Auto-chain nodes in order if no explicit edges
        if not self._edges:
            names = [n.name for n in self._nodes]
            for i in range(len(names) - 1):
                builder.add_edge(names[i], names[i + 1])
            builder.add_edge(names[-1], END)
        else:
            for src, tgt in self._edges:
                dest = END if tgt == "END" else tgt
                builder.add_edge(src, dest)

        self._compiled = builder.compile()
        return self._compiled

    def run(self, initial_state: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        graph = self._build()
        state = initial_state or {"messages": [], "context": {}, "metadata": {}}
        return graph.invoke(state)

    def stream(self, initial_state: Optional[dict[str, Any]] = None):
        graph = self._build()
        state = initial_state or {"messages": [], "context": {}, "metadata": {}}
        return graph.stream(state)

    @property
    def compiled(self):
        return self._build()

    @classmethod
    def from_skills_dir(cls, directory: str | Path, state_schema: Type = BaseState) -> "Graph":
        """
        Build a Graph from all skill files in a directory.
        Files are loaded alphabetically and chained in sequence.
        """
        from ..skills.loader import SkillLoader
        from ..skills.node import SkillNode

        specs = SkillLoader.from_dir(directory)
        if not specs:
            raise ValueError(f"No skill files found in: {directory}")

        g = cls(state_schema)
        for spec in specs:
            g.add(SkillNode(spec))
        return g

    @classmethod
    def from_skill_file(cls, path: str | Path, state_schema: Type = BaseState) -> "Graph":
        """Build a single-node Graph from a skill file."""
        from ..skills.loader import SkillLoader
        from ..skills.node import SkillNode

        spec = SkillLoader.from_file(path)
        g = cls(state_schema)
        g.add(SkillNode(spec))
        return g
