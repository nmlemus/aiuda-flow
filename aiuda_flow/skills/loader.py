"""
SkillLoader — loads skill specs from .yaml or .md files.

YAML format:
  name, description, model, system_prompt, tools, output_key, tags

Markdown format (frontmatter + body as system_prompt):
  ---
  name: MySkill
  model: claude-sonnet-4-6
  tools: [web_search]
  ---
  You are an expert researcher...
"""
import re
import yaml
from pathlib import Path
from typing import Optional


class SkillLoader:
    @staticmethod
    def from_file(path: str | Path) -> dict:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Skill file not found: {path}")

        if path.suffix in (".yaml", ".yml"):
            return SkillLoader._load_yaml(path)
        elif path.suffix == ".md":
            return SkillLoader._load_markdown(path)
        else:
            raise ValueError(f"Unsupported skill format: {path.suffix} (use .yaml or .md)")

    @staticmethod
    def _load_yaml(path: Path) -> dict:
        with open(path) as f:
            spec = yaml.safe_load(f)
        spec.setdefault("name", path.stem)
        spec.setdefault("source_file", str(path))
        return spec

    @staticmethod
    def _load_markdown(path: Path) -> dict:
        content = path.read_text()
        spec = {}

        # Extract YAML frontmatter
        frontmatter_match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
        if frontmatter_match:
            spec = yaml.safe_load(frontmatter_match.group(1)) or {}
            body = frontmatter_match.group(2).strip()
        else:
            body = content.strip()

        spec.setdefault("name", path.stem)
        spec.setdefault("source_file", str(path))

        # Markdown body becomes the system_prompt if not already defined
        if body and not spec.get("system_prompt"):
            spec["system_prompt"] = body

        return spec

    @staticmethod
    def from_dir(directory: str | Path) -> list[dict]:
        """Load all skill specs from a directory."""
        directory = Path(directory)
        skills = []
        for ext in ("*.yaml", "*.yml", "*.md"):
            for f in sorted(directory.glob(ext)):
                try:
                    skills.append(SkillLoader.from_file(f))
                except Exception as e:
                    print(f"Warning: could not load {f}: {e}")
        return skills
