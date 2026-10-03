"""Lesson 4b — Every asyncio action, one real-world example each, with a live clock.

Run:  uv run python lessons/lesson4b_asyncio_actions.py

Scenario for all examples: a restaurant kitchen with ONE chef (Python).
Each [x.xs] shows the time since that example started.
"""

import asyncio
import time

T0 = 0.0


def clock(msg: str) -> None:
    print(f"   [{time.perf_counter() - T0:4.1f}s] {msg}")


def section(title: str) -> None:
    global T0
    print(f"\n{'─' * 66}\n{title}\n{'─' * 66}")
    T0 = time.perf_counter()


# ---------------------------------------------------------------------------
# ACTION 1 + 2 + 3 + 4:  async def,  await,  asyncio.sleep,  asyncio.run
# ---------------------------------------------------------------------------
async def cook(dish: str, minutes: float) -> str:          # 1. async def  = a recipe
    clock(f"start {dish}")
    await asyncio.sleep(minutes)                            # 4. asyncio.sleep = oven time
    clock(f"done  {dish}")                                  #    (chef is FREE meanwhile)
    return f"{dish} 🍽"


async def action_await() -> None:
    section("ACTION 2 · await — cook one dish and wait for it")
    plate = await cook("dosa", 1)                           # 2. await = do it, get result
    clock(f"got {plate}")


async def action_sequential() -> None:
    section("TRAP · three awaits in a row = one after another (slow)")
    await cook("dosa", 1)
    await cook("idli", 1)
    await cook("vada", 1)
    clock("all served — 3 dishes took 3s")


# ---------------------------------------------------------------------------
# ACTION 5:  asyncio.gather — cook everything at the same time
# ---------------------------------------------------------------------------
async def action_gather() -> None:
    section("ACTION 5 · asyncio.gather — all dishes in the oven together")
    plates = await asyncio.gather(cook("dosa", 1), cook("idli", 1), cook("vada", 1))
    clock(f"served {plates} — 3 dishes took 1s")


# ---------------------------------------------------------------------------
# ACTION 6:  gather(..., return_exceptions=True) — one dish burns
# ---------------------------------------------------------------------------
async def cook_or_burn(dish: str) -> str:
    await asyncio.sleep(0.5)
    if dish == "biryani":
        raise ValueError(f"{dish} burned!")
    return f"{dish} 🍽"


async def action_gather_errors() -> None:
    section("ACTION 6 · gather(return_exceptions=True) — one dish burns")
    try:
        await asyncio.gather(cook_or_burn("dosa"), cook_or_burn("biryani"), cook_or_burn("vada"))
    except ValueError as e:
        clock(f"WITHOUT it: whole order fails -> {e}")

    results = await asyncio.gather(cook_or_burn("dosa"), cook_or_burn("biryani"),
                                   cook_or_burn("vada"), return_exceptions=True)
    clock(f"WITH it: {results}")
    served = [r for r in results if not isinstance(r, Exception)]
    clock(f"serve the good ones: {served}")


# ---------------------------------------------------------------------------
# ACTION 7:  asyncio.create_task — start now, collect later
# ---------------------------------------------------------------------------
async def action_create_task() -> None:
    section("ACTION 7 · create_task — put rice on, do other work, collect later")
    rice = asyncio.create_task(cook("rice", 2))     # starts cooking IMMEDIATELY in background
    clock("rice is cooking in the background; chef chops vegetables...")
    await asyncio.sleep(1)
    clock("vegetables chopped")
    plate = await rice                               # now wait for the rice to finish
    clock(f"got {plate} — total 2s, not 3s")


# ---------------------------------------------------------------------------
# ACTION 8:  asyncio.wait_for — timeout
# ---------------------------------------------------------------------------
async def action_wait_for() -> None:
    section("ACTION 8 · wait_for — customer waits max 1s, dish needs 3s")
    try:
        await asyncio.wait_for(cook("slow-cooked dal", 3), timeout=1)
    except TimeoutError:
        clock("TimeoutError — customer left, dish cancelled")


# ---------------------------------------------------------------------------
# ACTION 9:  asyncio.Semaphore — only 2 stoves
# ---------------------------------------------------------------------------
async def action_semaphore() -> None:
    section("ACTION 9 · Semaphore(2) — 5 dishes but only 2 stoves")
    stoves = asyncio.Semaphore(2)

    async def cook_on_stove(dish: str) -> str:
        async with stoves:                          # wait for a free stove
            return await cook(dish, 1)              # stove freed automatically after

    await asyncio.gather(*(cook_on_stove(d) for d in ["dosa", "idli", "vada", "upma", "pongal"]))
    clock("5 dishes, 2 at a time -> 3 rounds -> 3s")


# ---------------------------------------------------------------------------
# ACTION 10:  asyncio.as_completed — serve each dish the moment it's ready
# ---------------------------------------------------------------------------
async def action_as_completed() -> None:
    section("ACTION 10 · as_completed — serve in FINISH order, not order placed")
    orders = [cook("biryani", 1.5), cook("tea", 0.3), cook("dosa", 0.8)]
    for next_ready in asyncio.as_completed(orders):
        plate = await next_ready
        clock(f"  -> served {plate}")


# ---------------------------------------------------------------------------
# ACTION 11:  asyncio.TaskGroup — modern gather (Python 3.11+)
# ---------------------------------------------------------------------------
async def action_taskgroup() -> None:
    section("ACTION 11 · TaskGroup — modern, safer gather")
    async with asyncio.TaskGroup() as kitchen:
        dosa = kitchen.create_task(cook("dosa", 1))
        idli = kitchen.create_task(cook("idli", 1))
    # leaving the `async with` block waits for every task
    clock(f"served {dosa.result()} and {idli.result()} — 1s")


# ---------------------------------------------------------------------------
# ACTION 3: asyncio.run — open the restaurant (run everything above)
# ---------------------------------------------------------------------------
async def main() -> None:
    await action_await()
    await action_sequential()
    await action_gather()
    await action_gather_errors()
    await action_create_task()
    await action_wait_for()
    await action_semaphore()
    await action_as_completed()
    await action_taskgroup()


if __name__ == "__main__":
    asyncio.run(main())
