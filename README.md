# AI Engineer Journey

Hands-on path from **QA Automation Engineer → AI Engineer**.
Every module is a small, portfolio-ready project with tests — because testing
non-deterministic systems is where a QA background becomes an edge.

## Starting point (2026-09-28)

- Python: lower-intermediate (6/8 on assessment quiz)
- Strong: comprehensions, dicts, generators, `asyncio.gather`, pytest, venv
- Gaps: shared mutable state (default args, class vs instance attributes), HTTP APIs in Python
- Existing strengths: Playwright/TypeScript, API testing, CI pipelines

## Roadmap

| # | Module | Focus | Status |
|---|--------|-------|--------|
| 01 | [python-for-ai](01-python-for-ai/) | Mutability, dataclasses, Pydantic, httpx, async, first LLM call | 🟡 In progress |
| 02 | [rag-app](02-rag-app/) | Embeddings, chunking, vector store, retrieval quality | ⚪ Not started |
| 03 | [agents-tools](03-agents-tools/) | Tool use, MCP servers, multi-step agents | ⚪ Not started |
| 04 | [llm-evals](04-llm-evals/) | Eval harness, LLM-as-judge, regression suites in CI | ⚪ Not started |
| 05 | [guardrails](05-guardrails/) | Input/output validation, prompt-injection testing | ⚪ Not started |
| 06 | [capstone](06-capstone/) | End-to-end app: RAG + agent + evals + CI + deploy | ⚪ Not started |

## Progress log

| Date | What I did | What I learned |
|------|-----------|----------------|
| 2026-09-28 | Set up repo, Python assessment | Mutable defaults are created once at def time |
