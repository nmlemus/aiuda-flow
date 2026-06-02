"""
Demo: Research Pipeline with aiuda-flow
========================================
3-node pipeline:
  1. PlannerNode    — breaks the query into sub-questions
  2. ResearcherNode — answers each sub-question using Claude
  3. SynthesizerNode — produces a final structured report

Observability via Arize Phoenix (local embedded UI).
"""
import os
import sys
from typing import Any

# ── env ───────────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_API_KEY:
    print("⚠️  Set ANTHROPIC_API_KEY in .env or environment")
    sys.exit(1)

# ── aiuda-flow ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from aiuda_flow import Graph, Node, BaseState, setup_tracing
from typing_extensions import TypedDict, Annotated
import operator


# ── State schema for this pipeline ───────────────────────────────────────────
class ResearchState(TypedDict, total=False):
    query: str
    sub_questions: list[str]
    answers: Annotated[list[str], operator.add]
    report: str
    messages: Annotated[list[Any], operator.add]
    metadata: dict[str, Any]


# ── LLM helper ────────────────────────────────────────────────────────────────
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=1024)


# ── Nodes ─────────────────────────────────────────────────────────────────────
class PlannerNode(Node):
    """Breaks a research query into 3 focused sub-questions."""

    def run(self, state: ResearchState) -> dict:
        query = state.get("query", "What is LangGraph?")
        print(f"\n📋 [Planner] Query: {query}")

        response = llm.invoke(
            f"""Break this research query into exactly 3 focused sub-questions.
Return ONLY a numbered list, one per line.

Query: {query}"""
        )

        lines = [
            l.strip().lstrip("123. ").strip()
            for l in response.content.strip().split("\n")
            if l.strip()
        ][:3]

        print(f"   Sub-questions: {lines}")
        return {"sub_questions": lines}


class ResearcherNode(Node):
    """Answers each sub-question with a concise paragraph."""

    def run(self, state: ResearchState) -> dict:
        sub_questions = state.get("sub_questions", [])
        answers = []

        for q in sub_questions:
            print(f"\n🔍 [Researcher] Answering: {q}")
            response = llm.invoke(
                f"Answer this question in 2-3 sentences:\n\n{q}"
            )
            answers.append(f"Q: {q}\nA: {response.content.strip()}")
            print(f"   ✓ answered")

        return {"answers": answers}


class SynthesizerNode(Node):
    """Synthesizes answers into a structured report."""

    def run(self, state: ResearchState) -> dict:
        query = state.get("query", "")
        answers = state.get("answers", [])
        print(f"\n📝 [Synthesizer] Building report...")

        answers_text = "\n\n".join(answers)
        response = llm.invoke(
            f"""You are a research analyst. Given the following Q&A pairs about "{query}",
write a concise structured report with:
- Executive Summary (2-3 sentences)
- Key Findings (bullet points)
- Conclusion (1-2 sentences)

Q&A pairs:
{answers_text}"""
        )

        report = response.content.strip()
        print(f"\n{'='*60}")
        print("📊 FINAL REPORT")
        print('='*60)
        print(report)
        print('='*60)

        return {"report": report}


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "What is LangGraph and how does it compare to LangChain?"

    # Setup Arize Phoenix tracing (local embedded)
    print("🔭 Starting Arize Phoenix tracing...")
    try:
        setup_tracing(project_name="aiuda-flow-demo", local=True)
    except Exception as e:
        print(f"   (tracing unavailable: {e})")

    # Build and run the graph
    graph = (
        Graph(state_schema=ResearchState)
        .add(PlannerNode(), entry=True)
        .add(ResearcherNode())
        .add(SynthesizerNode())
    )

    print(f"\n🚀 Running research pipeline for: '{query}'\n")
    result = graph.run({"query": query, "answers": [], "messages": [], "metadata": {}})

    print(f"\n✅ Pipeline complete. State keys: {list(result.keys())}")
