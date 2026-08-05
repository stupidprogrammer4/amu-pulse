from datetime import UTC, datetime

from taskiq import InMemoryBroker

from events.bus import EventBus
from events.contracts.ping import Ping
from events.queues import App


async def test_publish_routes_to_the_named_app() -> None:
    # run the handler inline, so the assertions see it finish
    broker = InMemoryBroker(await_inplace=True)
    seen: list[dict[str, object]] = []

    @broker.task(task_name=Ping.name)
    async def handle(payload: dict[str, object]) -> None:
        seen.append(payload)

    await broker.startup()
    bus = EventBus(broker)

    await bus.publish(
        Ping(sent_at=datetime(2026, 8, 5, tzinfo=UTC), note="hello"),
        to=App.AI,
    )
    await broker.shutdown()

    assert len(seen) == 1
    assert seen[0]["note"] == "hello"
    assert Ping.model_validate(seen[0]).note == "hello"
