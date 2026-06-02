"""
aiuda-flow CLI

Usage:
  aiuda-flow run <graph_file.py>
  aiuda-flow skill list
  aiuda-flow skill install <author/repo>
  aiuda-flow skill install <author/repo/path/skill.yaml>
  aiuda-flow skill uninstall <author/repo>
  aiuda-flow skill run <skill_file.yaml> [--input "..."]
  aiuda-flow skill run <author/repo> [--input "..."]
"""
import sys
import json
import argparse
from pathlib import Path


def cmd_run(args):
    """Run a graph file."""
    graph_file = Path(args.file)
    if not graph_file.exists():
        print(f"Error: {graph_file} not found")
        sys.exit(1)
    namespace = {}
    exec(graph_file.read_text(), namespace)
    if "graph" in namespace:
        result = namespace["graph"].run()
        print(json.dumps(result, indent=2, default=str))
    else:
        print("Error: graph file must define a `graph` variable")
        sys.exit(1)


def cmd_skill_list(args):
    from .skills.registry import SkillRegistry
    registry = SkillRegistry()
    skills = registry.list()
    if not skills:
        print("No skills installed. Try: aiuda-flow skill install <author/repo>")
        return
    print(f"\n{'Ref':<30} {'Name':<25} {'Version':<10} Description")
    print("-" * 90)
    for s in skills:
        tags = ", ".join(s.get("tags", []))
        desc = s.get("description", "")[:40]
        print(f"{s['ref']:<30} {s['name']:<25} {s.get('version','?'):<10} {desc}")
    print()


def cmd_skill_install(args):
    from .skills.registry import SkillRegistry
    registry = SkillRegistry()
    node = registry.install(args.ref, branch=args.branch or "main")
    print(f"Node ready: {node.name}")


def cmd_skill_uninstall(args):
    from .skills.registry import SkillRegistry
    registry = SkillRegistry()
    registry.uninstall(args.ref)


def cmd_skill_run(args):
    """Run a skill directly — local file or installed ref."""
    from .skills.registry import SkillRegistry
    from pathlib import Path

    registry = SkillRegistry()
    path = Path(args.ref)

    if path.exists():
        node = registry.load_local(path)
    else:
        node = registry.get(args.ref)

    user_input = args.input or "Execute the task."
    state = {"input": user_input, "messages": [{"role": "user", "content": user_input}], "context": {}, "metadata": {}}
    result = node.run(state)
    output = result.get("last_output", result)
    print(output)


def main():
    parser = argparse.ArgumentParser(prog="aiuda-flow", description="aiuda-flow — portable GenAI workflow framework")
    subparsers = parser.add_subparsers(dest="command")

    # run
    run_p = subparsers.add_parser("run", help="Run a graph file")
    run_p.add_argument("file", help="Path to graph Python file")

    # skill
    skill_p = subparsers.add_parser("skill", help="Manage skills")
    skill_sub = skill_p.add_subparsers(dest="skill_command")

    skill_sub.add_parser("list", help="List installed skills")

    install_p = skill_sub.add_parser("install", help="Install a skill from GitHub")
    install_p.add_argument("ref", help="author/repo or author/repo/path/skill.yaml")
    install_p.add_argument("--branch", default="main", help="Git branch (default: main)")

    uninstall_p = skill_sub.add_parser("uninstall", help="Remove an installed skill")
    uninstall_p.add_argument("ref", help="author/repo")

    run_skill_p = skill_sub.add_parser("run", help="Run a skill directly")
    run_skill_p.add_argument("ref", help="Local file path or installed ref (author/repo)")
    run_skill_p.add_argument("--input", "-i", default=None, help="Input text for the skill")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "skill":
        if args.skill_command == "list":
            cmd_skill_list(args)
        elif args.skill_command == "install":
            cmd_skill_install(args)
        elif args.skill_command == "uninstall":
            cmd_skill_uninstall(args)
        elif args.skill_command == "run":
            cmd_skill_run(args)
        else:
            skill_p.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
