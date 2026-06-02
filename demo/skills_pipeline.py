"""
Demo: Build a pipeline entirely from skill files — no Python node code.

Usage:
  python demo/skills_pipeline.py
  python demo/skills_pipeline.py --input "Latest trends in AI agents"

Each .yaml/.md file in skills-registry/example-skills/ becomes a node.
The pipeline runs them in order: Researcher → Analyst → Writer.
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aiuda_flow import Graph


def main():
    parser = argparse.ArgumentParser(description="Skills pipeline demo")
    parser.add_argument("--input", "-i", default="Recent advances in multi-agent AI systems", help="Research topic")
    parser.add_argument("--skills-dir", default=str(Path(__file__).parent.parent / "skills-registry" / "example-skills"))
    args = parser.parse_args()

    print(f"\n🚀 aiuda-flow Skills Pipeline")
    print(f"   Topic: {args.input}")
    print(f"   Skills dir: {args.skills_dir}")
    print("─" * 60)

    # Build graph entirely from skill files
    graph = Graph.from_skills_dir(args.skills_dir)

    print(f"\n📦 Loaded {len(graph._nodes)} skill nodes:")
    for node in graph._nodes:
        print(f"   - {node.name} ({node._spec.get('description', '')})")

    print("\n⚙️  Running pipeline...\n")

    result = graph.run({
        "input": args.input,
        "messages": [{"role": "user", "content": args.input}],
        "context": {"topic": args.input},
        "metadata": {},
    })

    print("\n" + "─" * 60)
    print("✅ Pipeline complete\n")

    # Print outputs from each node
    for node in graph._nodes:
        key = node._spec.get("output_key", node.name + "_result")
        if key in result:
            print(f"\n### {node.name.upper()} OUTPUT")
            print(result[key])
            print()


if __name__ == "__main__":
    main()
