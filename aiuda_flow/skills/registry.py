"""
SkillRegistry — local index of installed skills + GitHub install/publish support.

Skills are stored at ~/.aiuda-flow/skills/<author>/<skill-name>/
Registry index: ~/.aiuda-flow/registry.yaml
"""
import json
import shutil
import subprocess
import yaml
from pathlib import Path
from typing import Optional
from .loader import SkillLoader
from .node import SkillNode


REGISTRY_DIR = Path.home() / ".aiuda-flow" / "skills"
REGISTRY_INDEX = Path.home() / ".aiuda-flow" / "registry.yaml"
GITHUB_RAW = "https://raw.githubusercontent.com"


class SkillRegistry:
    def __init__(self):
        REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
        self._index = self._load_index()

    def _load_index(self) -> dict:
        if REGISTRY_INDEX.exists():
            with open(REGISTRY_INDEX) as f:
                return yaml.safe_load(f) or {}
        return {"skills": {}}

    def _save_index(self):
        REGISTRY_INDEX.parent.mkdir(parents=True, exist_ok=True)
        with open(REGISTRY_INDEX, "w") as f:
            yaml.dump(self._index, f, default_flow_style=False)

    def list(self) -> list[dict]:
        """List all installed skills."""
        skills = []
        if not REGISTRY_DIR.exists():
            return skills
        for author_dir in sorted(REGISTRY_DIR.iterdir()):
            if not author_dir.is_dir():
                continue
            for skill_dir in sorted(author_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_file = self._find_skill_file(skill_dir)
                if skill_file:
                    try:
                        spec = SkillLoader.from_file(skill_file)
                        skills.append({
                            "ref": f"{author_dir.name}/{skill_dir.name}",
                            "name": spec.get("name", skill_dir.name),
                            "description": spec.get("description", ""),
                            "version": spec.get("version", "latest"),
                            "tags": spec.get("tags", []),
                        })
                    except Exception:
                        pass
        return skills

    def install(self, ref: str, branch: str = "main") -> SkillNode:
        """
        Install a skill from GitHub: `author/repo` or `author/repo/path/to/skill.yaml`

        Examples:
          registry.install("nmlemus/research-skill")
          registry.install("nmlemus/aiuda-flow-skills/skills/summarizer.yaml")
        """
        parts = ref.split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid ref '{ref}'. Use 'author/repo' or 'author/repo/path/skill.yaml'")

        author, repo = parts[0], parts[1]
        subpath = "/".join(parts[2:]) if len(parts) > 2 else f"{repo}.yaml"

        # Fetch raw file from GitHub
        url = f"{GITHUB_RAW}/{author}/{repo}/{branch}/{subpath}"
        try:
            import urllib.request
            with urllib.request.urlopen(url) as r:
                content = r.read().decode()
        except Exception as e:
            raise RuntimeError(f"Could not fetch skill from {url}: {e}")

        # Save locally
        dest_dir = REGISTRY_DIR / author / repo
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / Path(subpath).name
        dest_file.write_text(content)

        # Index it
        spec = SkillLoader.from_file(dest_file)
        skill_ref = f"{author}/{repo}"
        self._index.setdefault("skills", {})[skill_ref] = {
            "name": spec.get("name"),
            "description": spec.get("description", ""),
            "version": spec.get("version", "latest"),
            "local_path": str(dest_file),
        }
        self._save_index()

        print(f"✓ Installed skill '{spec.get('name')}' from {author}/{repo}")
        return SkillNode(spec)

    def get(self, ref: str) -> SkillNode:
        """Load an already-installed skill by ref."""
        skill_info = self._index.get("skills", {}).get(ref)
        if not skill_info:
            raise KeyError(f"Skill '{ref}' not installed. Run: aiuda-flow skill install {ref}")
        spec = SkillLoader.from_file(skill_info["local_path"])
        return SkillNode(spec)

    def uninstall(self, ref: str):
        """Remove a skill from local registry."""
        parts = ref.split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid ref: {ref}")
        author, repo = parts[0], parts[1]
        skill_dir = REGISTRY_DIR / author / repo
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
        self._index.get("skills", {}).pop(ref, None)
        self._save_index()
        print(f"✓ Uninstalled {ref}")

    def load_local(self, path: str) -> SkillNode:
        """Load a skill from a local file path (no install)."""
        spec = SkillLoader.from_file(path)
        return SkillNode(spec)

    def _find_skill_file(self, directory: Path) -> Optional[Path]:
        for ext in (".yaml", ".yml", ".md"):
            for f in directory.glob(f"*{ext}"):
                return f
        return None
