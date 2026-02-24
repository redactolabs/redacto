from redacto.events.config import EXCHANGES_AND_QUEUES
from redacto.events.models import Exchange, ExchangeType, Queue


class TestTopologyConfig:
    def test_has_exchanges(self):
        assert len(EXCHANGES_AND_QUEUES) > 0

    def test_platform_events_exchange(self):
        exchange = next((e for e in EXCHANGES_AND_QUEUES if e.name == Exchange.Name.PLATFORM_EVENTS), None)
        assert exchange is not None, "PLATFORM_EVENTS exchange not found in EXCHANGES_AND_QUEUES"
        assert exchange.name == Exchange.Name.PLATFORM_EVENTS
        assert exchange.type == ExchangeType.TOPIC

    def test_platform_events_has_queues(self):
        exchange = next((e for e in EXCHANGES_AND_QUEUES if e.name == Exchange.Name.PLATFORM_EVENTS), None)
        assert exchange is not None, "PLATFORM_EVENTS exchange not found in EXCHANGES_AND_QUEUES"
        queue_names = {q.name for q in exchange.queues}
        assert Queue.Name.USER_EVENTS in queue_names
        assert Queue.Name.VRM_EVENTS in queue_names

    def test_queues_have_bindings(self):
        exchange = next((e for e in EXCHANGES_AND_QUEUES if e.name == Exchange.Name.PLATFORM_EVENTS), None)
        assert exchange is not None, "PLATFORM_EVENTS exchange not found in EXCHANGES_AND_QUEUES"
        for queue in exchange.queues:
            assert len(queue.bindings) > 0, f"Queue {queue.name} has no bindings"

    def test_user_events_bindings(self):
        exchange = next((e for e in EXCHANGES_AND_QUEUES if e.name == Exchange.Name.PLATFORM_EVENTS), None)
        assert exchange is not None, "PLATFORM_EVENTS exchange not found in EXCHANGES_AND_QUEUES"
        user_queue = next((q for q in exchange.queues if q.name == Queue.Name.USER_EVENTS), None)
        assert user_queue is not None, "USER_EVENTS queue not found"
        routing_keys = {b.routing_key for b in user_queue.bindings}
        assert "vrm.#" in routing_keys

    def test_vrm_events_bindings(self):
        exchange = next((e for e in EXCHANGES_AND_QUEUES if e.name == Exchange.Name.PLATFORM_EVENTS), None)
        assert exchange is not None, "PLATFORM_EVENTS exchange not found in EXCHANGES_AND_QUEUES"
        vrm_queue = next((q for q in exchange.queues if q.name == Queue.Name.VRM_EVENTS), None)
        assert vrm_queue is not None, "VRM_EVENTS queue not found"
        routing_keys = {b.routing_key for b in vrm_queue.bindings}
        assert "vrm.#" in routing_keys
        assert "platform.documents.#" in routing_keys
