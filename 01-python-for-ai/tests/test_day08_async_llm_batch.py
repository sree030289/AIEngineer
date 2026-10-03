import asyncio
import json

import httpx
import pytest

from exercises.day03_pydantic_basics import TicketClassification
from exercises.day08_async_llm_batch import (
    classify_batch,
    classify_ticket,
    gather_limited,
    request_with_retry_async,
)


class FakeLLM:
    """A fake /classify endpoint that behaves like a real, imperfect LLM API.

    The ticket text decides the behaviour:
      contains "garbage" -> 200, but the completion has no usable JSON
      contains "flaky"   -> 503 the first time, then a normal answer
      contains "down"    -> always 500
      otherwise          -> 200 with chatty text wrapping valid JSON
    Also records how many requests are in flight at once.
    """

    def __init__(self, delay: float = 0.05):
        self.delay = delay
        self.in_flight = 0
        self.max_in_flight = 0
        self.calls: dict[str, int] = {}

    async def __call__(self, request: httpx.Request) -> httpx.Response:
        text = json.loads(request.content)["text"]
        self.calls[text] = self.calls.get(text, 0) + 1
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            await asyncio.sleep(self.delay)
            if "down" in text:
                return httpx.Response(500)
            if "flaky" in text and self.calls[text] == 1:
                return httpx.Response(503)
            if "garbage" in text:
                return httpx.Response(200, json={"completion": "I cannot classify this."})
            category = "bug" if "crash" in text else "feature" if "add" in text else "question"
            answer = json.dumps({"category": category, "priority": 2, "summary": f"Ticket: {text}"})
            return httpx.Response(200, json={"completion": f"Sure! Here you go:\n{answer}\nThanks."})
        finally:
            self.in_flight -= 1


def client_for(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url="https://llm.example.com",
                             transport=httpx.MockTransport(handler))


def spy_sleep():
    waits: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        waits.append(seconds)

    return waits, fake_sleep


# --- Exercise 1: gather_limited -----------------------------------------------
def _tracked_tasks(n: int, tracker: dict):
    async def work(i: int) -> int:
        tracker["now"] += 1
        tracker["max"] = max(tracker["max"], tracker["now"])
        await asyncio.sleep(0.02)
        tracker["now"] -= 1
        return i * 10

    return [lambda i=i: work(i) for i in range(n)]


def test_gather_limited_keeps_order():
    tracker = {"now": 0, "max": 0}
    assert asyncio.run(gather_limited(_tracked_tasks(6, tracker), limit=2)) == [0, 10, 20, 30, 40, 50]


def test_gather_limited_respects_limit():
    tracker = {"now": 0, "max": 0}
    asyncio.run(gather_limited(_tracked_tasks(20, tracker), limit=4))
    assert tracker["max"] == 4


def test_gather_limited_limit_larger_than_tasks():
    tracker = {"now": 0, "max": 0}
    assert asyncio.run(gather_limited(_tracked_tasks(3, tracker), limit=10)) == [0, 10, 20]
    assert tracker["max"] == 3


def test_gather_limited_empty():
    assert asyncio.run(gather_limited([], limit=3)) == []


# --- Exercise 2: request_with_retry_async -------------------------------------
# class ScriptedServer:
#     def __init__(self, *script):
#         self.script = list(script)
#         self.calls = 0

#     def __call__(self, request):
#         self.calls += 1
#         outcome = self.script.pop(0)
#         if isinstance(outcome, Exception):
#             raise outcome
#         if isinstance(outcome, tuple):
#             return httpx.Response(outcome[0], headers=outcome[1])
#         return httpx.Response(outcome, json={"attempt": self.calls})


# def _retry(server, **kwargs):
#     waits, fake_sleep = spy_sleep()
#     response = asyncio.run(request_with_retry_async(
#         client_for(server), "GET", "/x", sleep=fake_sleep, **kwargs))
#     return response, waits


# def test_async_retry_backoff_then_success():
#     response, waits = _retry(ScriptedServer(503, 429, 200))
#     assert response.json() == {"attempt": 3}
#     assert waits == [1.0, 2.0]


# def test_async_retry_uses_retry_after():
#     _, waits = _retry(ScriptedServer((429, {"Retry-After": "4"}), 200))
#     assert waits == [4.0]


# def test_async_retry_does_not_retry_client_errors():
#     server = ScriptedServer(401, 200)
#     with pytest.raises(httpx.HTTPStatusError):
#         _retry(server)
#     assert server.calls == 1


# def test_async_retry_transport_error_then_success():
#     response, waits = _retry(ScriptedServer(httpx.ReadTimeout("slow"), 200))
#     assert response.status_code == 200
#     assert waits == [1.0]


# def test_async_retry_gives_up():
#     server = ScriptedServer(503, 503)
#     with pytest.raises(httpx.HTTPStatusError):
#         _retry(server, max_attempts=2)
#     assert server.calls == 2


# # --- Exercise 3: classify_ticket ----------------------------------------------
# def test_classify_ticket_parses_buried_json():
#     result = asyncio.run(classify_ticket(client_for(FakeLLM()), "app crash on login"))
#     assert isinstance(result, TicketClassification)
#     assert result.category == "bug"
#     assert result.summary == "Ticket: app crash on login"


# def test_classify_ticket_garbage_reply_returns_none():
#     assert asyncio.run(classify_ticket(client_for(FakeLLM()), "garbage input")) is None


# def test_classify_ticket_retries_temporary_failure():
#     llm = FakeLLM()
#     waits, fake_sleep = spy_sleep()
#     result = asyncio.run(classify_ticket(client_for(llm), "flaky crash", sleep=fake_sleep))
#     assert result.category == "bug"
#     assert llm.calls["flaky crash"] == 2
#     assert waits == [1.0]


# def test_classify_ticket_raises_when_server_down():
#     _, fake_sleep = spy_sleep()
#     with pytest.raises(httpx.HTTPStatusError):
#         asyncio.run(classify_ticket(client_for(FakeLLM()), "server down", sleep=fake_sleep))


# # --- Exercise 4: classify_batch -----------------------------------------------
# TEXTS = [
#     "app crash on login",      # bug
#     "please add dark mode",    # feature
#     "how do I export data",    # question
#     "garbage reply",           # None: unusable completion
#     "flaky crash on save",     # bug, after one retry
#     "service down",            # None: 500 on every attempt
#     "add CSV export",          # feature
#     "crash when uploading",    # bug
#     "where is my invoice",     # question
#     "add SSO login",           # feature
#     "garbage again",           # None
#     "crash in settings",       # bug
# ]


# def test_classify_batch_results_in_order():
#     _, fake_sleep = spy_sleep()
#     results = asyncio.run(classify_batch(client_for(FakeLLM()), TEXTS, limit=4, sleep=fake_sleep))

#     categories = [r.category if r else None for r in results]
#     assert categories == ["bug", "feature", "question", None, "bug", None,
#                           "feature", "bug", "question", "feature", None, "bug"]


# def test_classify_batch_each_result_matches_its_own_text():
#     # Catches the classic lambda-in-a-loop bug (every task using the LAST text).
#     _, fake_sleep = spy_sleep()
#     results = asyncio.run(classify_batch(client_for(FakeLLM()), TEXTS, limit=4, sleep=fake_sleep))
#     for text, result in zip(TEXTS, results):
#         if result is not None:
#             assert result.summary == f"Ticket: {text}"


# def test_classify_batch_respects_limit():
#     llm = FakeLLM()
#     _, fake_sleep = spy_sleep()
#     asyncio.run(classify_batch(client_for(llm), TEXTS, limit=3, sleep=fake_sleep))
#     assert llm.max_in_flight == 3


# def test_classify_batch_empty():
#     assert asyncio.run(classify_batch(client_for(FakeLLM()), [])) == []
