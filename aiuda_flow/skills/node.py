"""
SkillNode — a Node built from a YAML/Markdown skill definition.
No code required: just a .yaml or .md file describes the agent behavior.
"""
from typing import Any
from ..core.node import Node


class SkillNode(Node):
    """A node whose behavior is defined by a skill spec (YAML/Markdown)."""

    def __init__(self, spec: dict):
        self._spec = spec
        self._name = spec.get("name", "skill").lower().replace(" ", "_")

    @property
    def name(self) -> str:
        return self._name

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute skill logic. Uses Claude API when model is specified,
        otherwise runs as a passthrough transform.
        """
        system_prompt = self._spec.get("system_prompt", "")
        tools = self._spec.get("tools", [])
        model = self._spec.get("model", "claude-sonnet-4-6")
        output_key = self._spec.get("output_key", self._name + "_result")

        # Try to call Claude if system_prompt is defined
        if system_prompt:
            try:
                import anthropic
                client = anthropic.Anthropic()

                messages = state.get("messages", [])
                if not messages:
                    # Build a default message from context
                    context = state.get("context", {})
                    user_input = state.get("input", context.get("input", "Execute the task."))
                    messages = [{"role": "user", "content": str(user_input)}]

                response = client.messages.create(
                    model=model,
                    max_tokens=2048,
                    system=system_prompt,
                    messages=messages,
                )
                result = response.content[0].text
                return {**state, output_key: result, "last_output": result}

            except ImportError:
                pass  # anthropic not installed, fall through to mock

        # Mock execution for testing without API keys
        description = self._spec.get("description", "No description")
        mock_result = f"[SkillNode:{self._name}] executed — {description}"
        return {**state, output_key: mock_result, "last_output": mock_result}
