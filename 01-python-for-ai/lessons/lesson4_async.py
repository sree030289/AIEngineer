"""Lesson 4 — async/await: do many slow things at the same time.

Run:  uv run python lessons/lesson4_async.py      (takes ~12 seconds — watch the timings)

You already know this from JavaScript / Playwright:
    JS:      await Promise.all([fetch(a), fetch(b)])
    Python:  await asyncio.gather(fetch(a), fetch(b))
"""

import asyncio
import time

import httpx


def step(title: str) -> None:
    print(f"\n{'=' * 64}\n{title}\n{'=' * 64}")


# ===========================================================================
# 1. The idea: waiting is wasted time
# ===========================================================================
# An LLM call spends ~99% of its time WAITING for the server.
# Sync code waits for each call to finish before starting the next.
# Async code starts the next call while the previous one is still waiting.
#
#   sync:   [call 1 ......][call 2 ......][call 3 ......]      3 seconds
#   async:  [call 1 ......]
#           [call 2 ......]                                    1 second
#           [call 3 ......]


# ===========================================================================
# 2. The three keywords
# ===========================================================================
async def make_coffee(name: str, seconds: float) -> str:   # `async def` = a coroutine function
    print(f"  start {name}")
    await asyncio.sleep(seconds)     # `await` = "pause me here, let others run meanwhile"
    print(f"  done  {name}")
    return f"{name} coffee"


async def one_after_another() -> None:
    step("2a. Sequential awaits — each waits for the previous one")
    start = time.perf_counter()
    a = await make_coffee("latte", 1)
    b = await make_coffee("mocha", 1)
    c = await make_coffee("espresso", 1)
    print(f"  results: {[a, b, c]}")
    print(f"  took {time.perf_counter() - start:.1f}s   <- no faster than normal code!")


async def all_at_once() -> None:
    step("2b. asyncio.gather — all at the same time (like Promise.all)")
    start = time.perf_counter()
    results = await asyncio.gather(
        make_coffee("latte", 1),
        make_coffee("mocha", 1),
        make_coffee("espresso", 1),
    )
    print(f"  results: {results}          <- same ORDER as you passed them in")
    print(f"  took {time.perf_counter() - start:.1f}s")


# ===========================================================================
# 3. The classic mistake: forgetting `await`
# ===========================================================================
async def forgot_await() -> None:
    step("3. Forgetting `await` gives you a coroutine object, not the result")
    result = make_coffee("cold brew", 0)        # no await!
    print(f"  result is: {result!r}")
    print("  -> nothing ran. Always `await` a coroutine (or pass it to gather).")
    result.close()                              # tidy up the unused coroutine


# ===========================================================================
# 4. Real HTTP: httpx.AsyncClient
# ===========================================================================
async def slow_server(request: httpx.Request) -> httpx.Response:
    await asyncio.sleep(0.5)                    # pretend every call takes 0.5s, like an LLM
    user_id = request.url.path.rsplit("/", 1)[-1]
    return httpx.Response(200, json={"id": int(user_id)})


async def http_demo() -> None:
    step("4. httpx.AsyncClient — 10 requests, sequential vs concurrent")
    transport = httpx.MockTransport(slow_server)
    # `async with` = the async version of `with`: closes the client when done
    async with httpx.AsyncClient(base_url="https://api.example.com", transport=transport) as client:
        start = time.perf_counter()
        for i in range(10):
            await client.get(f"/users/{i}")
        print(f"  sequential: {time.perf_counter() - start:.1f}s")

        start = time.perf_counter()
        responses = await asyncio.gather(*(client.get(f"/users/{i}") for i in range(10)))
        print(f"  concurrent: {time.perf_counter() - start:.1f}s")
        print(f"  ids in order: {[r.json()['id'] for r in responses]}")
    # The * "unpacks" the generator: gather(a, b, c) instead of gather([a, b, c]).


# ===========================================================================
# 5. Limiting concurrency: asyncio.Semaphore
# ===========================================================================
async def limited_demo() -> None:
    step("5. Semaphore — max 3 at a time (LLM APIs have rate limits!)")
    limit = asyncio.Semaphore(3)                # a "bouncer": only 3 inside at once
    in_flight = 0

    async def limited_call(i: int) -> int:
        nonlocal in_flight
        async with limit:                       # waits here if 3 are already inside
            in_flight += 1
            print(f"  call {i} running   (in flight: {in_flight})")
            await asyncio.sleep(0.3)
            in_flight -= 1
            return i

    start = time.perf_counter()
    await asyncio.gather(*(limited_call(i) for i in range(7)))
    print(f"  7 calls, max 3 at once -> 3 waves -> took {time.perf_counter() - start:.1f}s")


# ===========================================================================
# 6. When some calls fail: return_exceptions=True
# ===========================================================================
async def maybe_fail(i: int) -> int:
    await asyncio.sleep(0.1)
    if i == 2:
        raise ValueError(f"call {i} failed")
    return i * 10


async def failure_demo() -> None:
    step("6. One failure vs return_exceptions=True")
    try:
        await asyncio.gather(*(maybe_fail(i) for i in range(4)))
    except ValueError as e:
        print(f"  default: the whole gather raises -> {e!r}  (other results are lost)")

    results = await asyncio.gather(*(maybe_fail(i) for i in range(4)), return_exceptions=True)
    print(f"  return_exceptions=True -> {results}")
    print("  -> errors come back AS VALUES in the list; check with isinstance(r, Exception)")


# ===========================================================================
# 7. Timeouts: asyncio.wait_for
# ===========================================================================
async def timeout_demo() -> None:
    step("7. asyncio.wait_for — give up if it takes too long")
    try:
        await asyncio.wait_for(make_coffee("slow pour-over", 5), timeout=0.5)
    except TimeoutError:
        print("  TimeoutError after 0.5s — the slow task was cancelled")


# ===========================================================================
# Entry point: asyncio.run() starts the "event loop" that runs coroutines
# ===========================================================================
async def main() -> None:
    await one_after_another()
    await all_at_once()
    await forgot_await()
    await http_demo()
    await limited_demo()
    await failure_demo()
    await timeout_demo()


if __name__ == "__main__":
    asyncio.run(main())    # the ONLY place sync code calls into async code
