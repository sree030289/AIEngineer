"""Day 7 — async basics: await, gather, timeouts, partial failures.

Run:  uv run pytest tests/test_day07_async_basics.py -v
Learn first:  uv run python lessons/lesson4_async.py

Every function here is `async def`, so callers must `await` it.
The tests run them with asyncio.run(...) — you don't need to.

Same Ticket API as Day 5, but with httpx.AsyncClient. The only differences
from Day 5 code: `async def`, and `await` in front of every client call.
"""

import asyncio
from collections.abc import Awaitable
from typing import TypeVar

import httpx

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Exercise 1 — your first async function
# ---------------------------------------------------------------------------
async def fetch_json(client: httpx.AsyncClient, path: str) -> dict:
    """GET `path`, raise on 4xx/5xx, return the JSON body.

    It's Day 5's fetch_json with one extra word. Which word, and where?
    """
    response = await client.get(path)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# Exercise 2 — many requests at the same time
# ---------------------------------------------------------------------------
async def fetch_all(client: httpx.AsyncClient, paths: list[str]) -> list[dict]:
    """Fetch every path CONCURRENTLY and return the JSON bodies in the SAME ORDER as `paths`.

    If any request fails, let the exception propagate (default gather behaviour).
    An empty `paths` list returns [].

    Hint: asyncio.gather(*(fetch_json(client, p) for p in paths))
    The tests check it's actually concurrent — a for-loop of awaits will fail.
    """

    return  await asyncio.gather(*( fetch_json(client,p) for p in paths))



    


# ---------------------------------------------------------------------------
# Exercise 3 — don't wait forever
# ---------------------------------------------------------------------------
async def with_timeout(awaitable: Awaitable[T], seconds: float) -> T | None:
    """Await `awaitable`, but give up after `seconds`.

    Return its result if it finishes in time, otherwise return None.

    Hint: asyncio.wait_for(...) raises TimeoutError when time runs out.
    """
    try:
        return await asyncio.wait_for(awaitable,timeout=seconds)
    except:
        return None



# ---------------------------------------------------------------------------
# Exercise 4 — keep the good results when some calls fail
# ---------------------------------------------------------------------------
async def fetch_all_safe(client: httpx.AsyncClient, paths: list[str]) -> list[dict | None]:
    """Like fetch_all, but one bad path must not ruin the batch.

    Return a list in the same order as `paths`, where each item is:
      - the JSON body if that request succeeded
      - None if it failed with httpx.HTTPStatusError or httpx.TransportError

    Any OTHER exception type is a real bug — re-raise it, don't hide it.

    Hint: asyncio.gather(..., return_exceptions=True), then loop over the
    results and check each with isinstance(result, SomeErrorType).
    """

    responses =await asyncio.gather(*(fetch_json(client,p)for p in paths),return_exceptions=True)
    
    results = []
    for res in responses:
        if isinstance(res, (httpx.HTTPStatusError, httpx.TransportError)):
            results.append(None)        # expected failure → None
        elif isinstance(res, BaseException):
            raise res                   # anything else is a real bug → re-raise
        else:
            results.append(res)         # success → keep the JSON
    return results


