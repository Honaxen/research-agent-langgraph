# Research Agent (LangGraph)

A multi-step research agent built with LangGraph — state machine, conditional routing, and a human-in-the-loop approval checkpoint before anything gets saved.

🚧 **Work in progress.** This README tracks build progress and will be replaced with full documentation once complete.

---

## Why This Project

`multi-tool-agent` (previous project) is a single reasoning loop: think → call a tool → think again.

This project needs something a flat loop can't express cleanly:
- Looping back conditionally if research isn't good enough (up to 3 attempts)
- A pause point a human controls before anything gets saved
- Two different loop-back targets depending on what's rejected

---

## Planned Flow

```
research → summarize → quality_check
                            |-- insufficient --> research (loop, max 3 attempts)
                            |-- sufficient   --> human_approval
                                                     |-- approved --> save_file --> END
                                                     |-- rejected --> summarize (loop)
```

---

## Build Checklist

- [ ] `agent/state.py` — typed state shared across all graph nodes
- [ ] `agent/search_tools.py` — Wikipedia + DuckDuckGo search (free, no API key)
- [ ] `agent/llm.py` — Ollama chat wrapper
- [ ] `agent/graph.py` — nodes, conditional routing, graph assembly
- [ ] `agent/main.py` — CLI with human-approval pause/resume loop
- [ ] `tests/test_graph.py` — routing logic + file saving tests
- [ ] `requirements.txt`
- [ ] `.gitignore`
- [ ] Test with Ollama end-to-end
- [ ] Replace this README with full documentation

---

## Planned Structure

```
research-agent-langgraph/
├── agent/
│   ├── __init__.py
│   ├── state.py
│   ├── search_tools.py
│   ├── llm.py
│   ├── graph.py
│   └── main.py
├── tests/
│   └── test_graph.py
├── requirements.txt
└── .gitignore
```

---

## Stack

Python · LangGraph · Ollama · Wikipedia API · DuckDuckGo API · pytest

---

## Related Projects

- [multi-tool-agent](https://github.com/Honaxen/multi-tool-agent) — single-loop ReAct agent

---

## Author

[Honaxen](https://github.com/Honaxen)