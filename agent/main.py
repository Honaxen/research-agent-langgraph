"""
main.py — CLI for the research agent.

LangGraph's `human_approval` node doesn't block by itself — the interface
layer is responsible for:
  1. Running the graph until it reaches human_approval
  2. Showing the summary and asking the human
  3. Re-invoking the graph with human_approved set

This file owns that loop.

Usage:
    python3 -m agent.main "history of the Roman aqueducts"
"""

import sys
from agent.graph import build_graph
from agent.state import ResearchState

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
GREEN  = "\033[32m"
CYAN   = "\033[36m"
YELLOW = "\033[33m"


def run_research(topic: str):
    app = build_graph()

    state: ResearchState = {
        "topic": topic,
        "queries_tried": [],
        "sources": [],
        "summary": "",
        "is_sufficient": False,
        "attempt_count": 0,
        "human_approved": None,
        "final_path": "",
    }

    print(f"{BOLD}Researching:{RESET} {topic}\n")

    while True:
        # Run until the graph reaches human_approval or finishes
        result = app.invoke(state)
        state = {**state, **result}

        if state.get("final_path"):
            print(f"\n{GREEN}{BOLD}Saved →{RESET} {state['final_path']}")
            return state

        # We've stopped at human_approval — show summary, ask for input
        print(f"{CYAN}{BOLD}--- Sources gathered ---{RESET}")
        for s in state["sources"]:
            if s["content"]:
                print(f"{DIM}  [{s['engine']}] {s['title']}{RESET}")

        print(f"\n{CYAN}{BOLD}--- Draft summary ---{RESET}")
        print(state["summary"])

        answer = input(f"\n{YELLOW}{BOLD}Approve and save this summary? (y/n):{RESET} ").strip().lower()
        state["human_approved"] = answer.startswith("y")

        if not state["human_approved"]:
            print(f"{DIM}Rejected — regenerating summary...{RESET}\n")


def main():
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = input(f"{BOLD}What topic should I research?{RESET} ").strip()

    if not topic:
        print("Please provide a topic.")
        sys.exit(1)

    try:
        run_research(topic)
    except ConnectionError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()