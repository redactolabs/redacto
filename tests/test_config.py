from redacto.events.config import EXCHANGES_AND_QUEUES
from redacto.events.models import Exchange, ExchangeType, Queue


class TestTopologyConfig:
    def test_has_exchanges(self):
        assert len(EXCHANGES_AND_QUEUES) > 0

    def test_platform_events_exchange(self):
        exchange = EXCHANGES_AND_QUEUES[0]
        assert exchange.name == Exchange.Name.PLATFORM_EVENTS
        assert exchange.type == ExchangeType.TOPIC

    def test_platform_events_has_queues(self):
        exchange = EXCHANGES_AND_QUEUES[0]
        queue_names = {q.name for q in exchange.queues}
        assert Queue.Name.USER_EVENTS in queue_names
        assert Queue.Name.VRM_EVENTS in queue_names

    def test_queues_have_bindings(self):
        exchange = EXCHANGES_AND_QUEUES[0]
        for queue in exchange.queues:
            assert len(queue.bindings) > 0, f"Queue {queue.name} has no bindings"

    def test_user_events_bindings(self):
        exchange = EXCHANGES_AND_QUEUES[0]
        user_queue = next(q for q in exchange.queues if q.name == Queue.Name.USER_EVENTS)
        routing_keys = {b.routing_key for b in user_queue.bindings}
        assert "vrm.#" in routing_keys

    def test_vrm_events_bindings(self):
        exchange = EXCHANGES_AND_QUEUES[0]
        vrm_queue = next(q for q in exchange.queues if q.name == Queue.Name.VRM_EVENTS)
        routing_keys = {b.routing_key for b in vrm_queue.bindings}
        assert "vrm.#" in routing_keys
        assert "platform.documents.#" in routing_keys
