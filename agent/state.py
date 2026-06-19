"""
state.py — The shared state passed between every node in the graph.

In LangGraph, state is a TypedDict that every node reads from and writes to.
This is the core difference from the manual ReAct loop in multi-tool-agent:
state is explicit and structured, not just a growing message list.
"""

from typing import TypedDict, Annotated
import operator


class ResearchState(TypedDict):
    """
    The full state of one research run.

    Fields:
        topic: the original user topic
        queries_tried: list of search queries already attempted
        sources: list of (title, content, source_engine) tuples gathered so far
        summary: the current draft summary
        is_sufficient: whether quality_check decided we have enough sources
        attempt_count: how many research loops we've done (safety limit)
        human_approved: None until the human responds, then True/False
        final_path: path to the saved file, set only after save_file runs
    """
    topic: str
    queries_tried: Annotated[list[str], operator.add]
    sources: Annotated[list[dict], operator.add]
    summary: str
    is_sufficient: bool
    attempt_count: int
    human_approved: bool | None
    final_path: str