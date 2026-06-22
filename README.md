# Research Agent (LangGraph)

A multi-step research agent built with LangGraph — state machine, conditional routing,
and a human-in-the-loop approval checkpoint before anything gets saved.

---

## What makes this different from multi-tool-agent

`multi-tool-agent` is a single reasoning loop: think → call a tool → think again.

This project needed something a flat loop can't express cleanly:

- **Looping back conditionally** — if research isn't good enough, go research again (up to 3 times), not just once.
- **A pause point a human controls** — the graph stops, shows you the draft, and only continues once you approve or reject it.
- **Two different loop-back targets** — rejecting a summary goes back to `summarize`, not all the way back to `research`.

LangGraph expresses this as a graph with conditional edges instead of nested if/else logic.

```
research → summarize → quality_check
                            |-- insufficient --> research (loop, max 3 attempts)
                            |-- sufficient   --> human_approval
                                                     |-- approved --> save_file --> END
                                                     |-- rejected --> summarize (loop)
```

---

## Project Structure

```
research-agent-langgraph/
├── agent/
│   ├── __init__.py
│   ├── state.py         — typed state shared across all nodes
│   ├── search_tools.py  — Wikipedia + DuckDuckGo (free, no API key)
│   ├── llm.py           — Ollama chat wrapper
│   ├── graph.py         — nodes, conditional routing, graph assembly
│   └── main.py          — CLI with the human-approval pause/resume loop
├── tests/
│   └── test_graph.py    — routing logic + file saving tests
├── requirements.txt
└── .gitignore
```

---

## Getting Started

```bash
pip install -r requirements.txt
ollama serve
ollama pull gemma3:12b   # or any model you have
```

### Run

```bash
python3 -m agent.main "history of the Roman aqueducts"
```

The agent will:
1. Search for sources (Wikipedia first, DuckDuckGo as fallback)
2. Summarize what it found
3. Check if it has enough sources — if not, search again automatically
4. Show you the draft summary and ask: **approve or reject?**
5. If rejected, regenerate the summary and ask again
6. If approved, save to `reports/<topic>.md`

### Run tests

```bash
pytest tests/ -v
```

---

## Stack

Python · LangGraph · Ollama · Wikipedia API · DuckDuckGo API · pytest

---

## What I Learned

A flat ReAct loop can't express "go back to step 2, not step 1."
LangGraph's conditional edges make branching logic a property of the graph,
not a tangle of if/else inside one function.

State should be explicit, not implicit in a growing message history.
Typing the state (`ResearchState`) made it obvious what every node reads and writes —
bugs showed up as type mismatches, not silent failures three steps later.

Human-in-the-loop isn't a special framework feature — it's just a graph node
that does nothing on its own and waits for the interface layer to decide
what happens next. The interrupt/resume pattern in `main.py` is the actual mechanism.

---

## Related projects

## Related projects

- [multi-tool-agent](https://github.com/Honaxen/multi-tool-agent) — single-loop ReAct agent
- [rag-system-from-scratch](https://github.com/Honaxen/rag-system-from-scratch) — RAG pipeline
- [rag-evaluation-framework](https://github.com/Honaxen/rag-evaluation-framework) — evaluate any RAG pipeline

---

## Author

[Honaxen](https://github.com/Honaxen)