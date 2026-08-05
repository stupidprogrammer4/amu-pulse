from events.queues import App, all_queues, queue, queue_name


def test_each_app_gets_its_own_inbox() -> None:
    assert queue_name(App.API) == "api.events"
    assert queue_name(App.AI) == "ai.events"


def test_a_queue_routes_on_its_own_name() -> None:
    inbox = queue(App.AI)

    assert inbox.name == "ai.events"
    assert inbox.routing_key in (None, "ai.events")


def test_a_publisher_knows_every_inbox() -> None:
    names = {q.name for q in all_queues()}

    assert names == {"api.events", "ai.events"}
