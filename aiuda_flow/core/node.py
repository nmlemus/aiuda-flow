from abc import ABC, abstractmethod
from typing import Any


class Node(ABC):
    """Base class for all aiuda-flow nodes."""

    @property
    def name(self) -> str:
        return self.__class__.__name__.lower().replace("node", "")

    @abstractmethod
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute node logic. Receives state, returns state updates."""
        ...

    def __call__(self, state: dict[str, Any]) -> dict[str, Any]:
        return self.run(state)
