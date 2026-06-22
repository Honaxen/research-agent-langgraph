"""
graph.py — The LangGraph state machine.

Flow:
  research → summarize → quality_check
                              |-- insufficient --> research (loop, max 3 attempts)
                              |-- sufficient   --> human_approval
                                                       |-- approved --> save_file --> END
                                                       |-- rejected --> summarize (loop)

This is the key upgrade over multi-tool-agent's manual while-loop:
- Conditional edges are declared, not hand-written if/else chains.
- State is typed and explicit (see state.py).
- A human approval checkpoint is a first-class graph node, not bolted on.
"""

from langgraph.graph import StateGraph, END

from agent.state import ResearchState
from agent.search_tools import search
from agent.llm import call_llm

MAX_RESEARCH_ATTEMPTS = 3
MIN_SOURCES_REQUIRED = 2


# ─────────────────────────────────────────────
# Node: research
# ─────────────────────────────────────────────

def research_node(state: ResearchState) -> dict:
    """Generate a search query for this attempt and fetch a source."""
    topic = state["topic"]
    attempt = state["attempt_count"]

    if attempt == 0:
        query = topic
    else:
        # Ask the LLM for a follow-up query to fill gaps
        existing_titles = [s["title"] for s in state["sources"]]
        prompt = (
            f"Topic: {topic}\n"
            f"Already searched: {state['queries_tried']}\n"
            f"Sources found so far: {existing_titles}\n\n"
            "Suggest ONE new, different search query to find more information "
            "on this topic. Reply with ONLY the query text, nothing else."
        )
        query = call_llm(prompt).strip().strip('"')

    result = search(query)

    new_source = {
        "title": result.title,
        "content": result.content,
        "engine": result.source,
        "query": query,
    }

    return {
        "queries_tried": [query],
        "sources": [new_source] if result.content else [],
        "attempt_count": attempt + 1,
    }


# ─────────────────────────────────────────────
# Node: summarize
# ─────────────────────────────────────────────

def summarize_node(state: ResearchState) -> dict:
    """Condense all gathered sources into one summary."""
    sources_text = "\n\n".join(
        f"[{s['title']} — via {s['engine']}]\n{s['content']}"
        for s in state["sources"]
        if s["content"]
    )

    if not sources_text:
        return {"summary": f"No information could be found on '{state['topic']}'."}

    prompt = (
        f"Topic: {state['topic']}\n\n"
        f"Sources:\n{sources_text}\n\n"
        "Write a clear, well-organized summary (3-5 paragraphs) of this topic "
        "based ONLY on the sources above. Do not add outside knowledge. "
        "Write in your own words."
    )

    summary = call_llm(prompt)
    return {"summary": summary}


# ─────────────────────────────────────────────
# Node: quality_check (router, not a real node — see routing fn below)
# ─────────────────────────────────────────────

def _quality_check(state: ResearchState) -> str:
    """
    Conditional router: decide whether to research more or move to approval.
    Returns the name of the next node.
    """
    valid_sources = [s for s in state["sources"] if s["content"]]

    if len(valid_sources) >= MIN_SOURCES_REQUIRED:
        return "human_approval"

    if state["attempt_count"] >= MAX_RESEARCH_ATTEMPTS:
        # Give up gathering more — proceed with what we have
        return "human_approval"

    return "research"


# ─────────────────────────────────────────────
# Node: human_approval
# ─────────────────────────────────────────────

def human_approval_node(state: ResearchState) -> dict:
    """
    Present the summary and pause for human input.
    LangGraph requires at least one field written per node,
    so we set is_sufficient=True to signal research is done.
    The CLI layer reads state["summary"] and asks the human.
    """
    return {"is_sufficient": True}


def _approval_router(state: ResearchState) -> str:
    if state.get("human_approved") is True:
        return "save_file"
    elif state.get("human_approved") is False:
        return "summarize"
    else:
        # Should not happen if interface layer is correct — default to ending
        return "save_file"


# ─────────────────────────────────────────────
# Node: save_file
# ─────────────────────────────────────────────

def save_file_node(state: ResearchState) -> dict:
    """Write the approved summary to a markdown file."""
    import re

    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", state["topic"].lower())[:50]
    path = f"reports/{safe_name}.md"

    import os
    os.makedirs("reports", exist_ok=True)

    sources_list = "\n".join(
        f"- [{s['title']}] (via {s['engine']}) — query: \"{s['query']}\""
        for s in state["sources"]
        if s["content"]
    )

    content = (
        f"# {state['topic']}\n\n"
        f"{state['summary']}\n\n"
        f"---\n\n## Sources\n\n{sources_list}\n"
    )

    with open(path, "w") as f:
        f.write(content)

    return {"final_path": path}


# ─────────────────────────────────────────────
# Build the graph
# ─────────────────────────────────────────────

def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("research", research_node)
    graph.add_node("summarize", summarize_node)
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("save_file", save_file_node)

    graph.set_entry_point("research")

    graph.add_edge("research", "summarize")

    graph.add_conditional_edges(
        "summarize",
        _quality_check,
        {
            "research": "research",
            "human_approval": "human_approval",
        },
    )

    graph.add_conditional_edges(
        "human_approval",
        _approval_router,
        {
            "save_file": "save_file",
            "summarize": "summarize",
        },
    )

    graph.add_edge("save_file", END)

    return graph.compile()