# 01 — Python for AI

Two weeks of focused Python, test-first. Each day has an exercise file with
stubs/bugs and a test file that fails until you fix it. **Don't edit the tests.**

## How to work

```bash
cd 01-python-for-ai
uv sync                                   # one-time: create .venv and install pytest
uv run pytest tests/test_day01_mutability.py -v   # run one day's tests
uv run pytest                             # run everything
```

Workflow per exercise: read the docstring → run the test (red) → write code → test (green)
→ write 2–3 lines in `notes/` about what surprised you.

## Plan

| Days | Topic | Exercise | Done |
|------|-------|----------|------|
| 1 | References, mutability, copies | `exercises/day01_mutability.py` | ✅ |
| 2 | Class vs instance attrs, `@dataclass` | `exercises/day02_chat_history.py` | ✅ |
| 3 | Pydantic basics: parse messy LLM JSON | `exercises/day03_pydantic_basics.py` | ✅ |
| 4 | Validators, nested models, tool schema, retry feedback | `exercises/day04_pydantic_advanced.py` | ☐ |
| 5 | `httpx` client, dependency injection, validating responses | `exercises/day05_http_client.py` | ✅ |
| 6 | Retries: status classification, backoff, Retry-After | `exercises/day06_retries.py` | ✅ |
| 7 | async basics: `await`, `gather`, timeouts, partial failures | `exercises/day07_async_basics.py` | ☐ |
| 8 | Rate-limited batch LLM classification + async retries | `exercises/day08_async_llm_batch.py` | ☐ |
| 9 | Env vars, `.env`, secrets, `pydantic-settings` | `exercises/day09_config.py` | ☐ |
| 10 | pytest fixtures (`conftest.py`), `tmp_path`, `monkeypatch`, ruff | `tests/conftest.py` | ☐ |
| 11–14 | First LLM app: call, stream, structured output | *coming next* | ☐ |

## Key concept for Days 1–2

In Python, **variables are labels pointing to objects**, not boxes holding values.

```python
a = [1, 2]
b = a          # b points to the SAME list
b.append(3)
print(a)       # [1, 2, 3]  ← a "changed" too
```

- Default argument values are evaluated **once**, when `def` runs — not on each call.
- Attributes defined on the class body are **shared by all instances**.
- `list(x)` / `x.copy()` make a **shallow** copy; nested objects are still shared.
  `copy.deepcopy(x)` copies all the way down.

## Key concept for Days 3–4

A **dataclass** stores data. A **Pydantic model** stores data *and checks it* at runtime.

```python
class Ticket(BaseModel):
    priority: int = Field(ge=1, le=5)

Ticket(priority="3")    # OK  -> priority == 3   (safe conversion)
Ticket(priority=9)      # ValidationError: Input should be less than or equal to 5
```

Why AI engineers use it everywhere: LLM output is **untrusted input**. Treat it like
an API response you're testing — validate the shape before anything else touches it.

| You want to... | Use |
|---|---|
| Declare types + limits | type hints + `Field(ge=, le=, min_length=, ...)` |
| Restrict to fixed values | `Literal["a", "b"]` |
| Parse a JSON string | `Model.model_validate_json(text)` |
| Parse a dict | `Model.model_validate(data)` |
| Clean/check one field | `@field_validator("name")` |
| Check rules across fields | `@model_validator(mode="after")` |
| Tell the LLM the shape | `Model.model_json_schema()` |
| Tell the LLM what it got wrong | `ValidationError.errors()` |

## Key concept for Days 5–6

Lesson first: `uv run python lessons/lesson3_httpx.py`

| Postman | httpx |
|---|---|
| Collection base URL | `httpx.Client(base_url=...)` |
| Auth / headers tab | `headers={"Authorization": "Bearer ..."}` |
| Send | `client.get(path)` / `client.post(path, json=body)` |
| Status / body | `response.status_code` / `response.json()` |
| Test "status is 2xx" | `response.raise_for_status()` |

**httpx never raises on 4xx/5xx by itself** — you call `raise_for_status()`.

Two families of errors:
- `httpx.HTTPStatusError` — the server answered with an error code (retry only 429/5xx/529)
- `httpx.TransportError` — no answer at all: timeouts, connection failures (retry)

**Dependency injection:** functions *receive* the `client` and the `sleep` function instead
of creating them. Tests pass in fakes (`httpx.MockTransport`, a list's `.append`), so they run
instantly and never touch the network.

## Key concept for Days 7–8

Lesson first: `uv run python lessons/lesson4_async.py`

| JavaScript | Python |
|---|---|
| `async function f()` | `async def f():` |
| `await f()` | `await f()` |
| `await Promise.all([a(), b()])` | `await asyncio.gather(a(), b())` |
| `Promise.allSettled` | `asyncio.gather(..., return_exceptions=True)` |
| (top-level await) | `asyncio.run(main())` — the one bridge from sync to async |

- Async helps when code **waits** (HTTP, LLM calls) — not for heavy computation.
- Forgetting `await` gives you a *coroutine object*, and nothing runs.
- Inside async code use `asyncio.sleep`, never `time.sleep` (it freezes everything).
- `asyncio.Semaphore(n)` = max `n` at a time — how you stay under API rate limits.
- `asyncio.wait_for(x, timeout=s)` = give up after `s` seconds.

## Key concept for Days 9–10

**Day 9 — secrets never go in code.** Live demo: `uv run python lessons/lesson6_config_secrets.py`

- An environment variable is named text that lives outside your code. It is always a string.
- `os.environ["X"]` crashes if missing; `os.environ.get("X")` returns `None`.
- Put real keys in `.env` (git-ignored). Commit only `.env.example` with fake values.
- `pydantic-settings` reads, converts and validates all config in one class.
- `SecretStr` hides a value when printed; `.get_secret_value()` reveals it on purpose.
- Priority: argument > real env var > `.env` file > default.

**Day 10 — fixtures.** Live demo: `uv run pytest lessons/test_lesson7_fixtures_demo.py -v -s`

- A fixture is a function that prepares something; a test asks for it by naming it as a parameter.
- Each test gets a fresh copy. Fixtures can use other fixtures. Shared ones live in `conftest.py`.
- `yield` inside a fixture = setup before, cleanup after (runs even if the test fails).
- Built-ins: `tmp_path` (temp folder), `monkeypatch` (temporary changes, auto-undone).

**Ruff** (linter + formatter): `uv run ruff check .` finds problems, `uv run ruff check . --fix`
fixes the safe ones, `uv run ruff format .` reformats. Config is in `pyproject.toml`.

**uv cheat sheet:** `uv sync` (install from lockfile) · `uv add pkg` (add a dependency) ·
`uv add --dev pkg` (dev-only) · `uv run cmd` (run inside the project's environment).
