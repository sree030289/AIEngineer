import httpx
import pytest

from exercises.day06_retries import (
    backoff_delay,
    classify_status,
    request_with_retry,
    retry_after_seconds,
)


# --- Exercise 1: classify_status ----------------------------------------------
@pytest.mark.parametrize("code", [200, 201, 204])
def test_success_codes(code):
    assert classify_status(code) == "ok"


@pytest.mark.parametrize("code", [429, 500, 502, 503, 504, 529])
def test_retryable_codes(code):
    assert classify_status(code) == "retry"


@pytest.mark.parametrize("code", [400, 401, 403, 404, 422])
def test_failing_codes(code):
    assert classify_status(code) == "fail"


# --- Exercise 2: backoff_delay ------------------------------------------------
@pytest.mark.parametrize("attempt, expected", [(0, 1.0), (1, 2.0), (2, 4.0), (3, 8.0)])
def test_backoff_doubles(attempt, expected):
    assert backoff_delay(attempt) == expected


def test_backoff_is_capped():
    assert backoff_delay(10) == 30.0


def test_backoff_custom_base_and_cap():
    assert backoff_delay(2, base=0.5, cap=100) == 2.0
    assert backoff_delay(5, base=0.5, cap=10) == 10.0


# # --- Exercise 3: retry_after_seconds ------------------------------------------
# @pytest.mark.parametrize("value, expected", [("5", 5.0), ("0.5", 0.5), ("120", 120.0)])
# def test_retry_after_numeric(value, expected):
#     assert retry_after_seconds(httpx.Response(429, headers={"Retry-After": value})) == expected


# def test_retry_after_missing():
#     assert retry_after_seconds(httpx.Response(503)) is None


# def test_retry_after_not_a_number():
#     response = httpx.Response(503, headers={"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"})
#     assert retry_after_seconds(response) is None


# # --- Exercise 4: request_with_retry -------------------------------------------
# class ScriptedServer:
#     """Fake server that replays a script of outcomes, one per request.

#     Each item is either a status code (int) or an exception instance to raise.
#     Optionally a (status, headers) tuple.
#     """

#     def __init__(self, *script):
#         self.script = list(script)
#         self.calls = 0

#     def __call__(self, request: httpx.Request) -> httpx.Response:
#         self.calls += 1
#         outcome = self.script.pop(0)
#         if isinstance(outcome, Exception):
#             raise outcome
#         if isinstance(outcome, tuple):
#             status, headers = outcome
#             return httpx.Response(status, headers=headers, json={})
#         return httpx.Response(outcome, json={"attempt": self.calls})


# def run(server: ScriptedServer, **kwargs):
#     waits: list[float] = []
#     client = httpx.Client(base_url="https://api.example.com",
#                           transport=httpx.MockTransport(server))
#     response = request_with_retry(client, "GET", "/v1/thing", sleep=waits.append, **kwargs)
#     return response, waits


# def test_success_first_time_no_waiting():
#     server = ScriptedServer(200)
#     response, waits = run(server)
#     assert response.status_code == 200
#     assert server.calls == 1
#     assert waits == []


# def test_retries_then_succeeds_with_exponential_backoff():
#     server = ScriptedServer(503, 429, 200)
#     response, waits = run(server)
#     assert response.json() == {"attempt": 3}
#     assert waits == [1.0, 2.0]


# def test_uses_retry_after_header_when_present():
#     server = ScriptedServer((429, {"Retry-After": "7"}), 200)
#     _, waits = run(server)
#     assert waits == [7.0]


# def test_does_not_retry_client_errors():
#     server = ScriptedServer(401, 200)
#     with pytest.raises(httpx.HTTPStatusError):
#         run(server)
#     assert server.calls == 1


# def test_gives_up_after_max_attempts():
#     server = ScriptedServer(503, 503, 503, 200)
#     with pytest.raises(httpx.HTTPStatusError) as exc:
#         run(server, max_attempts=3)
#     assert exc.value.response.status_code == 503
#     assert server.calls == 3


# def test_retries_on_timeout_then_succeeds():
#     server = ScriptedServer(httpx.ReadTimeout("slow"), 200)
#     response, waits = run(server)
#     assert response.status_code == 200
#     assert waits == [1.0]


# def test_reraises_transport_error_after_last_attempt():
#     server = ScriptedServer(httpx.ConnectError("down"), httpx.ConnectError("still down"))
#     with pytest.raises(httpx.ConnectError):
#         run(server, max_attempts=2)
#     assert server.calls == 2


# def test_passes_extra_kwargs_to_the_request():
#     seen = {}

#     def server(request):
#         seen["method"] = request.method
#         seen["body"] = request.content
#         return httpx.Response(200)

#     client = httpx.Client(transport=httpx.MockTransport(server))
#     request_with_retry(client, "POST", "https://api.example.com/x", json={"a": 1}, sleep=lambda s: None)
#     assert seen == {"method": "POST", "body": b'{"a":1}'}
