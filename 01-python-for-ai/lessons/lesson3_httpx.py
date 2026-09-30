"""Lesson 3 — httpx: calling APIs from Python (the "Postman in code" lesson).

Run:
    uv run python lessons/lesson3_httpx.py

Part B talks to YOUR FastAPI app from Lesson 2. Start it first in another terminal:
    uv run fastapi dev lessons/lesson2_fastapi.py
(If it isn't running, Part B prints a hint and the rest still works.)
"""

import httpx


def step(title: str) -> None:
    print(f"\n{'=' * 64}\n{title}\n{'=' * 64}")


# ===========================================================================
# PART A — A fake server, so you can see every behaviour without the network
# ===========================================================================
# httpx.MockTransport lets you plug in a Python function AS the server.
# The function receives the request and returns a response.
# This is exactly how the Day 5–6 tests work — no internet needed.
def fake_server(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/users/1":
        return httpx.Response(200, json={"id": 1, "name": "Sree"})
    if request.url.path == "/users" and request.method == "POST":
        import json
        body = json.loads(request.content)
        return httpx.Response(201, json={"id": 2, **body})
    if request.url.path == "/busy":
        return httpx.Response(503, json={"error": "overloaded"}, headers={"Retry-After": "2"})
    return httpx.Response(404, json={"error": "not found"})


client = httpx.Client(
    base_url="https://api.example.com",            # every path is relative to this
    headers={"Authorization": "Bearer test-key"},  # sent with EVERY request
    timeout=10.0,                                  # seconds; never call APIs without one
    transport=httpx.MockTransport(fake_server),    # <- only in tests / this lesson
)

# ---------------------------------------------------------------------------
step("1. GET — like clicking Send in Postman")
# ---------------------------------------------------------------------------
response = client.get("/users/1")
print("status code: ", response.status_code)       # 200
print("json body:   ", response.json())            # dict: {'id': 1, 'name': 'Sree'}
print("full URL:    ", response.request.url)       # base_url + path
print("header sent: ", response.request.headers["authorization"])

# ---------------------------------------------------------------------------
step("2. POST with a JSON body")
# ---------------------------------------------------------------------------
response = client.post("/users", json={"name": "Asha"})   # json= serialises the dict
print(response.status_code, response.json())              # 201 {'id': 2, 'name': 'Asha'}

# ---------------------------------------------------------------------------
step("3. Error status codes do NOT raise by themselves")
# ---------------------------------------------------------------------------
response = client.get("/nope")
print("status:", response.status_code, "| is_success:", response.is_success)
# httpx happily returns a 404 response. YOU must decide what to do with it.

# raise_for_status() turns 4xx/5xx into an exception:
try:
    response.raise_for_status()
except httpx.HTTPStatusError as e:
    print("HTTPStatusError:", e.response.status_code, e.request.url)

# ---------------------------------------------------------------------------
step("4. Reading response headers (e.g. Retry-After on 429/503)")
# ---------------------------------------------------------------------------
response = client.get("/busy")
print(response.status_code, "Retry-After =", response.headers.get("Retry-After"))
# Servers use this header to say "wait N seconds, then try again".

# ---------------------------------------------------------------------------
step("5. The two families of errors")
# ---------------------------------------------------------------------------
print("""
  The server ANSWERED, but with an error code      The request never got a proper answer
  ─────────────────────────────────────────        ──────────────────────────────────────
  httpx.HTTPStatusError  (from raise_for_status)    httpx.TransportError  (parent class)
    429 Too Many Requests  -> retry later             ├─ httpx.TimeoutException -> retry
    500/502/503/504        -> retry                   └─ httpx.ConnectError     -> retry
    529 (Anthropic overloaded) -> retry
    400/401/403/404/422    -> DON'T retry: your request is wrong, it will fail again
""")


def broken_network(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectTimeout("simulated timeout", request=request)


with httpx.Client(transport=httpx.MockTransport(broken_network)) as flaky:
    try:
        flaky.get("https://api.example.com/anything")
    except httpx.TransportError as e:
        print(f"Caught {type(e).__name__}: {e}")

# `with httpx.Client(...) as c:` closes the connection pool automatically at the end.
client.close()


# ===========================================================================
# PART B — Now for real: call the FastAPI app you built in Lesson 2
# ===========================================================================
step("6. Real HTTP call to your own Lesson 2 API")
try:
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=5.0) as api:
        created = api.post("/tickets", json={"category": "bug", "priority": 2,
                                             "summary": "Created from httpx!"})
        print("POST /tickets ->", created.status_code, created.json())

        invalid = api.post("/tickets", json={"category": "outage", "priority": 9})
        print("POST invalid  ->", invalid.status_code)
        for err in invalid.json()["detail"]:
            print("   ", err["loc"], err["msg"])

        print("GET /tickets  ->", api.get("/tickets").json())
except httpx.ConnectError:
    print("Server not running. In another terminal run:")
    print("    uv run fastapi dev lessons/lesson2_fastapi.py")
    print("then run this lesson again.")
