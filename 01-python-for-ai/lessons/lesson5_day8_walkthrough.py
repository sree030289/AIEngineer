"""Lesson 5 — Day 8 walkthrough: each exercise explained with a live demo AND its answer.

Run:  uv run python lessons/lesson5_day8_walkthrough.py

The 4 exercises build ONE pipeline. Read it bottom-up:

    classify_batch          (Ex 4)  50 tickets, max N at a time, failures -> None
      └ gather_limited      (Ex 1)  the "bouncer": limits how many run at once
      └ classify_ticket     (Ex 3)  ONE ticket: call the LLM, parse the reply
          └ request_with_retry_async (Ex 2)  the call itself, retried on 503/429/timeouts
          └ safe_parse      (Day 3)  JSON buried in chatty text -> validated object
"""

import asyncio
import json
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # so `exercises` is importable

from exercises.day03_pydantic_basics import safe_parse  # noqa: E402
from exercises.day06_retries import backoff_delay, classify_status, retry_after_seconds  # noqa: E402

T0 = 0.0


def clock(msg: str) -> None:
    print(f"   [{time.perf_counter() - T0:4.1f}s] {msg}")


def section(title: str) -> None:
    global T0
    print(f"\n{'═' * 70}\n{title}\n{'═' * 70}")
    T0 = time.perf_counter()


# ═══════════════════════════════════════════════════════════════════════════
# EXERCISE 1 — gather_limited
# ═══════════════════════════════════════════════════════════════════════════
# THE ANSWER:
async def gather_limited(tasks, limit):
    semaphore = asyncio.Semaphore(limit)           # a bouncer holding `limit` wristbands

    async def run_one(task):
        async with semaphore:                      # take a wristband (or wait for one)
            return await task()                    # create the coroutine NOW, run it
                                                   # wristband returned automatically

    return await asyncio.gather(*(run_one(t) for t in tasks))   # results keep input order


async def demo_ex1() -> None:
    section("EX 1 · gather_limited — 6 jobs, but only 2 may run at once")

    async def job(name: str) -> str:
        clock(f"  start {name}")
        await asyncio.sleep(1)                     # pretend: one LLM call takes 1s
        clock(f"  done  {name}")
        return name.upper()

    # Each task is a ZERO-ARGUMENT FUNCTION that makes a coroutine when called.
    tasks = [lambda n=n: job(n) for n in ["a", "b", "c", "d", "e", "f"]]
    results = await gather_limited(tasks, limit=2)
    clock(f"results (input order): {results}")
    print("   -> 6 jobs / 2 at a time = 3 rounds = 3s   (without the limit: 1s, but a 429 error)")


# ═══════════════════════════════════════════════════════════════════════════
# EXERCISE 2 — request_with_retry_async
# ═══════════════════════════════════════════════════════════════════════════
# THE ANSWER: Day 6's function with 3 changes marked  ← (async, await, await)
async def request_with_retry_async(                              # ← async def
    client, method, url, *, max_attempts=3, sleep=asyncio.sleep, **kwargs
):
    for attempt in range(max_attempts):
        is_last_attempt = attempt == max_attempts - 1
        try:
            response = await client.request(method, url, **kwargs)   # ← await
        except httpx.TransportError:
            if is_last_attempt:
                raise
            await sleep(backoff_delay(attempt))                      # ← await
            continue
        outcome = classify_status(response.status_code)
        if outcome == "ok":
            return response
        if outcome == "fail" or is_last_attempt:
            response.raise_for_status()
        server_wait = retry_after_seconds(response)
        await sleep(server_wait if server_wait is not None else backoff_delay(attempt))   # ← await


async def demo_ex2() -> None:
    section("EX 2 · request_with_retry_async — a server that fails twice, then works")
    script = [503, (429, {"Retry-After": "4"}), 200]     # what the fake server does, in order
    n = 0

    def flaky_server(request: httpx.Request) -> httpx.Response:
        nonlocal n
        outcome = script[n]
        n += 1
        status, headers = outcome if isinstance(outcome, tuple) else (outcome, {})
        clock(f"server got request #{n} -> replies {status}")
        return httpx.Response(status, headers=headers, json={"ok": status == 200})

    async def fake_sleep(seconds: float) -> None:        # spy: record the wait, don't actually wait
        clock(f"  (would sleep {seconds}s — skipped so this demo is instant)")

    async with httpx.AsyncClient(base_url="https://llm.example.com",
                                 transport=httpx.MockTransport(flaky_server)) as client:
        response = await request_with_retry_async(client, "POST", "/classify",
                                                  json={"text": "hi"}, sleep=fake_sleep)
    clock(f"final answer: {response.status_code} {response.json()}")
    print("   -> 1st failure: no Retry-After header -> backoff 1s.  2nd: server said 4 -> we wait 4.")


# ═══════════════════════════════════════════════════════════════════════════
# EXERCISE 3 — classify_ticket
# ═══════════════════════════════════════════════════════════════════════════
# THE ANSWER:
async def classify_ticket(client, text, sleep=asyncio.sleep):
    response = await request_with_retry_async(client, "POST", "/classify",
                                              json={"text": text}, sleep=sleep)
    completion = response.json()["completion"]       # the LLM's reply text
    return safe_parse(completion)                    # Day 3: dig out + validate the JSON, or None


def fake_llm(request: httpx.Request) -> httpx.Response:
    text = json.loads(request.content)["text"]
    if "garbage" in text:
        return httpx.Response(200, json={"completion": "Sorry, I can't classify that."})
    category = "bug" if "crash" in text else "feature" if "add" in text else "question"
    answer = json.dumps({"category": category, "priority": 2, "summary": f"Ticket: {text}"})
    return httpx.Response(200, json={"completion": f"Sure! Here you go:\n{answer}\nHope that helps!"})


async def demo_ex3() -> None:
    section("EX 3 · classify_ticket — one ticket, step by step")
    async with httpx.AsyncClient(base_url="https://llm.example.com",
                                 transport=httpx.MockTransport(fake_llm)) as client:
        raw = (await client.post("/classify", json={"text": "app crash on login"})).json()
        print("   STEP 1  server replies with JSON that has a 'completion' string:")
        print(f"           {raw}\n")
        print("   STEP 2  inside that string, the useful JSON is buried in chatty text.")
        print("   STEP 3  safe_parse (your Day 3 code) digs it out and validates it:\n")
        ticket = await classify_ticket(client, "app crash on login")
        print(f"           {ticket!r}")
        print(f"           type = {type(ticket).__name__}   <- a real validated object, not text\n")
        bad = await classify_ticket(client, "garbage input")
        print(f"   When the reply is useless: classify_ticket returns {bad!r}   (not a crash)")


# ═══════════════════════════════════════════════════════════════════════════
# EXERCISE 4 — classify_batch
# ═══════════════════════════════════════════════════════════════════════════
# THE ANSWER:
async def classify_batch(client, texts, limit=5, sleep=asyncio.sleep):
    async def one(text):                                           # small helper takes `text`
        try:                                                       # as a PARAMETER (safe!)
            return await classify_ticket(client, text, sleep=sleep)
        except (httpx.HTTPStatusError, httpx.TransportError):     # expected failures only
            return None                                            # one bad ticket ≠ dead batch

    tasks = [lambda t=text: one(t) for text in texts]              # `t=text` freezes each text
    return await gather_limited(tasks, limit)


async def demo_ex4() -> None:
    section("EX 4a · THE TRAP — lambdas in a loop all see the LAST value")
    wrong = [lambda: text for text in ["ticket-1", "ticket-2", "ticket-3"]]
    print(f"   lambda: text            -> {[f() for f in wrong]}      ❌ all the same!")
    right = [lambda t=text: t for text in ["ticket-1", "ticket-2", "ticket-3"]]
    print(f"   lambda t=text: t        -> {[f() for f in right]}  ✅")
    print("   A lambda looks up `text` when it RUNS (after the loop ended), not when created.")
    print("   `t=text` copies the value at creation time.")

    section("EX 4b · classify_batch — 8 tickets, max 3 at a time, some bad")

    in_flight = peak = 0

    async def slow_llm(request: httpx.Request) -> httpx.Response:
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        text = json.loads(request.content)["text"]
        clock(f"  LLM call starts: {text!r:28} (in flight: {in_flight})")
        await asyncio.sleep(1)
        in_flight -= 1
        if "down" in text:
            return httpx.Response(500)                   # server error -> retries -> gives up
        return fake_llm(request)

    async def fake_sleep(_: float) -> None:
        pass                                             # skip retry waits to keep the demo short

    texts = ["app crash on login", "please add dark mode", "how do I export?", "garbage input",
             "service down", "crash when saving", "add CSV export", "where is my invoice"]
    async with httpx.AsyncClient(base_url="https://llm.example.com",
                                 transport=httpx.MockTransport(slow_llm)) as client:
        results = await classify_batch(client, texts, limit=3, sleep=fake_sleep)

    print()
    for text, result in zip(texts, results):
        shown = result.category if result else None
        print(f"   {text!r:28} -> {shown}")
    print(f"\n   peak concurrent calls: {peak}   (limit was 3)")
    print("   None = reply unusable (garbage) OR server failed after retries (down)")
    print("   Same ORDER as the input, and the bad tickets did not stop the batch.")


async def main() -> None:
    await demo_ex1()
    await demo_ex2()
    await demo_ex3()
    await demo_ex4()


if __name__ == "__main__":
    asyncio.run(main())
