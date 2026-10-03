"""Tests call async functions with asyncio.run(...) — the bridge from normal code into async."""

import asyncio
import time

import httpx
import pytest

from exercises.day07_async_basics import fetch_all, fetch_all_safe, fetch_json, with_timeout

DELAY = 0.2   # every fake request takes this long


async def slow_server(request: httpx.Request) -> httpx.Response:
    """/items/<n> -> {"n": n} after DELAY.  /missing/... -> 404.  /boom/... -> connection error."""
    await asyncio.sleep(DELAY)
    kind, value = request.url.path.strip("/").split("/")
    if kind == "missing":
        return httpx.Response(404, json={"detail": "not found"})
    if kind == "boom":
        raise httpx.ConnectError("server unreachable", request=request)
    return httpx.Response(200, json={"n": int(value)})


def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url="https://api.example.com",
                             transport=httpx.MockTransport(slow_server))


# --- Exercise 1: fetch_json ---------------------------------------------------
def test_fetch_json_returns_body():
    assert asyncio.run(fetch_json(client(), "/items/7")) == {"n": 7}


def test_fetch_json_raises_on_404():
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(fetch_json(client(), "/missing/1"))


def test_fetch_json_is_a_coroutine_function():
    # Calling it without await must NOT run the request — it returns a coroutine.
    coro = fetch_json(client(), "/items/1")
    assert asyncio.iscoroutine(coro)
    coro.close()


# # --- Exercise 2: fetch_all ----------------------------------------------------
def test_fetch_all_keeps_order():
    paths = [f"/items/{n}" for n in [5, 3, 9, 1]]
    assert asyncio.run(fetch_all(client(), paths)) == [{"n": 5}, {"n": 3}, {"n": 9}, {"n": 1}]


def test_fetch_all_is_concurrent():
    paths = [f"/items/{n}" for n in range(10)]
    start = time.perf_counter()
    asyncio.run(fetch_all(client(), paths))
    elapsed = time.perf_counter() - start
    # Sequential would take 10 * 0.2 = 2.0s. Concurrent takes ~0.2s.
    assert elapsed < DELAY * 4, f"took {elapsed:.2f}s — requests ran one after another"


def test_fetch_all_empty():
    assert asyncio.run(fetch_all(client(), [])) == []


def test_fetch_all_propagates_errors():
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(fetch_all(client(), ["/items/1", "/missing/2"]))


# --- Exercise 3: with_timeout -------------------------------------------------
async def _slow_value(value, seconds):
    await asyncio.sleep(seconds)
    return value


def test_with_timeout_returns_result_in_time():
    assert asyncio.run(with_timeout(_slow_value("done", 0.05), seconds=1)) == "done"


def test_with_timeout_returns_none_when_too_slow():
    start = time.perf_counter()
    assert asyncio.run(with_timeout(_slow_value("late", 5), seconds=0.1)) is None
    assert time.perf_counter() - start < 1, "must give up after ~0.1s, not wait 5s"


def test_with_timeout_works_with_http():
    assert asyncio.run(with_timeout(fetch_json(client(), "/items/4"), seconds=1)) == {"n": 4}


# --- Exercise 4: fetch_all_safe -----------------------------------------------
def test_fetch_all_safe_mixed_results():
    paths = ["/items/1", "/missing/2", "/items/3", "/boom/4"]
    assert asyncio.run(fetch_all_safe(client(), paths)) == [{"n": 1}, None, {"n": 3}, None]


def test_fetch_all_safe_is_concurrent():
    paths = [f"/items/{n}" for n in range(10)]
    start = time.perf_counter()
    asyncio.run(fetch_all_safe(client(), paths))
    assert time.perf_counter() - start < DELAY * 4


def test_fetch_all_safe_does_not_hide_real_bugs():
    async def buggy_server(request):
        raise KeyError("a bug in our own code")

    buggy = httpx.AsyncClient(base_url="https://api.example.com",
                              transport=httpx.MockTransport(buggy_server))
    with pytest.raises(KeyError):
        asyncio.run(fetch_all_safe(buggy, ["/items/1"]))
