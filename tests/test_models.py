import pytest
from pydantic import ValidationError

from redacto.events.models import (
    Consumer,
    Exchange,
    ExchangeType,
    Queue,
    QueueBinding,
)


class TestExchangeType:
    def test_values(self):
        assert ExchangeType.DIRECT == "direct"
        assert ExchangeType.TOPIC == "topic"
        assert ExchangeType.HEADERS == "headers"
        assert ExchangeType.FANOUT == "fanout"

    def test_str(self):
        assert str(ExchangeType.TOPIC) == "topic"


class TestQueueBinding:
    def test_create(self):
        binding = QueueBinding(routing_key="vrm.#")
        assert binding.routing_key == "vrm.#"

    def test_missing_routing_key(self):
        with pytest.raises(ValidationError):
            QueueBinding()


class TestQueue:
    def test_create_with_defaults(self):
        q = Queue(name=Queue.Name.USER_EVENTS)
        assert q.name == Queue.Name.USER_EVENTS
        assert q.durable is True
        assert q.auto_delete is False
        assert q.exclusive is False
        assert q.bindings == []

    def test_create_with_bindings(self):
        q = Queue(
            name=Queue.Name.VRM_EVENTS,
            bindings=[QueueBinding(routing_key="vrm.#")],
        )
        assert len(q.bindings) == 1
        assert q.bindings[0].routing_key == "vrm.#"

    def test_queue_name_enum_str(self):
        assert str(Queue.Name.USER_EVENTS) == "user.events"
        assert str(Queue.Name.VRM_EVENTS) == "vrm.events"

    def test_invalid_queue_name(self):
        with pytest.raises(ValidationError):
            Queue(name="nonexistent.queue")


class TestConsumer:
    def test_create(self):
        def cb(*args):
            return None

        consumer = Consumer(
            queue_name=Queue.Name.USER_EVENTS,
            callback=cb,
        )
        assert consumer.queue_name == Queue.Name.USER_EVENTS
        assert consumer.callback is cb
        assert consumer.auto_ack is True

    def test_auto_ack_override(self):
        def cb(*args):
            return None

        consumer = Consumer(
            queue_name=Queue.Name.VRM_EVENTS,
            callback=cb,
            auto_ack=False,
        )
        assert consumer.auto_ack is False


class TestExchange:
    def test_create_with_defaults(self):
        ex = Exchange(name=Exchange.Name.PLATFORM_EVENTS)
        assert ex.name == Exchange.Name.PLATFORM_EVENTS
        assert ex.type == ExchangeType.TOPIC
        assert ex.durable is True
        assert ex.auto_delete is False
        assert ex.queues == []

    def test_create_with_queues(self):
        ex = Exchange(
            name=Exchange.Name.PLATFORM_EVENTS,
            queues=[Queue(name=Queue.Name.USER_EVENTS)],
        )
        assert len(ex.queues) == 1

    def test_exchange_name_str(self):
        assert str(Exchange.Name.PLATFORM_EVENTS) == "platform.events"
