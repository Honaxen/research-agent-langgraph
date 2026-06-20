"""
tests/test_graph.py — Unit tests for routing logic and search tools.

These test the deterministic parts (routing functions, file saving)
without needing Ollama or network access.
"""

import os
import shutil
import pytest

from agent.graph import _quality_check, _approval_router, save_file_node
from agent.search_tools import SearchResult


# ─────────────────────────────────────────────
# quality_check routing tests
# ─────────────────────────────────────────────

class TestQualityCheck:
    def base_state(self, **overrides):
        state = {
            "topic": "test topic",
            "queries_tried": [],
            "sources": [],
            "summary": "",
            "is_sufficient": False,
            "attempt_count": 0,
            "human_approved": None,
            "final_path": "",
        }
        state.update(overrides)
        return state

    def test_insufficient_sources_routes_to_research(self):
        state = self.base_state(
            sources=[{"title": "a", "content": "x", "engine": "wiki", "query": "q"}],
            attempt_count=1,
        )
        assert _quality_check(state) == "research"

    def test_sufficient_sources_routes_to_approval(self):
        state = self.base_state(
            sources=[
                {"title": "a", "content": "x", "engine": "wiki", "query": "q1"},
                {"title": "b", "content": "y", "engine": "ddg", "query": "q2"},
            ],
            attempt_count=2,
        )
        assert _quality_check(state) == "human_approval"

    def test_max_attempts_forces_approval_even_if_insufficient(self):
        state = self.base_state(
            sources=[{"title": "a", "content": "x", "engine": "wiki", "query": "q"}],
            attempt_count=3,
        )
        assert _quality_check(state) == "human_approval"

    def test_empty_content_sources_dont_count(self):
        state = self.base_state(
            sources=[
                {"title": "a", "content": "", "engine": "none", "query": "q1"},
                {"title": "b", "content": "", "engine": "none", "query": "q2"},
            ],
            attempt_count=1,
        )
        assert _quality_check(state) == "research"


# ─────────────────────────────────────────────
# approval routing tests
# ─────────────────────────────────────────────

class TestApprovalRouter:
    def base_state(self, **overrides):
        state = {
            "topic": "test",
            "queries_tried": [],
            "sources": [],
            "summary": "",
            "is_sufficient": False,
            "attempt_count": 0,
            "human_approved": None,
            "final_path": "",
        }
        state.update(overrides)
        return state

    def test_approved_routes_to_save(self):
        state = self.base_state(human_approved=True)
        assert _approval_router(state) == "save_file"

    def test_rejected_routes_to_summarize(self):
        state = self.base_state(human_approved=False)
        assert _approval_router(state) == "summarize"


# ─────────────────────────────────────────────
# save_file_node tests
# ─────────────────────────────────────────────

class TestSaveFile:
    def teardown_method(self):
        if os.path.exists("reports"):
            shutil.rmtree("reports")

    def test_creates_file_with_correct_content(self):
        state = {
            "topic": "Roman Aqueducts",
            "queries_tried": ["roman aqueducts"],
            "sources": [
                {"title": "Aqueduct", "content": "...", "engine": "wikipedia", "query": "roman aqueducts"}
            ],
            "summary": "Roman aqueducts carried water using gravity.",
            "is_sufficient": True,
            "attempt_count": 1,
            "human_approved": True,
            "final_path": "",
        }
        result = save_file_node(state)
        assert os.path.exists(result["final_path"])

        with open(result["final_path"]) as f:
            content = f.read()
        assert "Roman Aqueducts" in content
        assert "gravity" in content
        assert "Aqueduct" in content

    def test_filename_is_sanitized(self):
        state = {
            "topic": "C++ vs Python: A Comparison!",
            "queries_tried": [],
            "sources": [],
            "summary": "test",
            "is_sufficient": True,
            "attempt_count": 1,
            "human_approved": True,
            "final_path": "",
        }
        result = save_file_node(state)
        # No special characters should survive
        filename = result["final_path"].split("/")[-1]
        assert "+" not in filename
        assert ":" not in filename
        assert "!" not in filename


# ─────────────────────────────────────────────
# SearchResult basic test
# ─────────────────────────────────────────────

class TestSearchResult:
    def test_dataclass_fields(self):
        r = SearchResult(query="q", source="wikipedia", title="t", content="c")
        assert r.query == "q"
        assert r.source == "wikipedia"