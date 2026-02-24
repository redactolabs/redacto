import json
from unittest.mock import MagicMock, patch

import pytest

from redacto.events.client import RabbitMQClient, close_client, get_client
from redacto.events.events import EventType
from redacto.events.exceptions import ConfigurationError, UnsupportedEventTypeError
from redacto.events.models import Consumer, Exchange, Queue
import redacto.events.client as client_module


@pytest.fixture
def mock_pika():
    with patch("redacto.events.client.pika") as mock:
        mock_connection = MagicMock()
        mock_publisher_channel = MagicMock()
        mock_consumer_channel = MagicMock()

        mock.URLParameters.return_value = MagicMock()
        mock.BlockingConnection.return_value = mock_connection
        mock_connection.channel.side_effect = [
            mock_publisher_channel,
            mock_consumer_channel,
        ]
        mock_connection.is_closed = False
        mock_publisher_channel.is_open = True

        yield {
            "pika": mock,
            "connection": mock_connection,
            "publisher_channel": mock_publisher_channel,
            "consumer_channel": mock_consumer_channel,
        }


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the global singleton between tests."""
    client_module._client = None
    yield
    client_module._client = None


class TestRabbitMQClientInit:
    def test_missing_url_raises(self):
        with pytest.raises(ConfigurationError, match="rabbitmq_url is required"):
            RabbitMQClient(rabbitmq_url="")

    def test_none_url_raises(self):
        with pytest.raises(ConfigurationError, match="rabbitmq_url is required"):
            RabbitMQClient(rabbitmq_url=None)

    def test_successful_init(self, mock_pika):
        client = RabbitMQClient(rabbitmq_url="amqp://localhost")
        assert client.rabbitmq_url == "amqp://localhost"
        assert client.source == "undefined"
        assert client.heartbeat == 60
        assert client.connection is mock_pika["connection"]

    def test_custom_params(self, mock_pika):
        client = RabbitMQClient(
            rabbitmq_url="amqp://localhost",
            source="test-service",
            heartbeat=30,
            connection_attempts=5,
            retry_delay=2.0,
            prefetch_count=10,
        )
        assert client.source == "test-service"
        assert client.heartbeat == 30
        assert client.connection_attempts == 5
        assert client.retry_delay == 2.0
        assert client.prefetch_count == 10

    def test_setup_topology_called(self, mock_pika):
        RabbitMQClient(rabbitmq_url="amqp://localhost")
        mock_pika["publisher_channel"].exchange_declare.assert_called()
        mock_pika["consumer_channel"].queue_declare.assert_called()
        mock_pika["consumer_channel"].queue_bind.assert_called()


class TestPublishEvent:
    def test_publish_valid_event(self, mock_pika):
        client = RabbitMQClient(rabbitmq_url="amqp://localhost")
        client.publish_event(
            routing_key="vrm.form",
            type=EventType.VRM_FORM_SUBMITTED,
            data={"form_id": "123"},
        )
        mock_pika["publisher_channel"].basic_publish.assert_called_once()
        call_kwargs = mock_pika["publisher_channel"].basic_publish.call_args
        assert call_kwargs.kwargs["exchange"] == Exchange.Name.PLATFORM_EVENTS
        assert call_kwargs.kwargs["routing_key"] == "vrm.form"

        body = json.loads(call_kwargs.kwargs["body"])
        assert body["type"] == "vrm.form.submitted"
        assert body["source"] == "undefined"
        assert body["specversion"] == "1.0"
        assert body["data"] == {"form_id": "123"}

    def test_publish_unsupported_event_raises(self, mock_pika):
        """Runtime validation rejects types not in ALL_EVENTS, even if passed as a raw string
        (Python doesn't enforce type hints at runtime)."""
        client = RabbitMQClient(rabbitmq_url="amqp://localhost")
        with pytest.raises(UnsupportedEventTypeError, match=r"nonexistent\.event"):
            client.publish_event(
                routing_key="test",
                type="nonexistent.event",
            )

    def test_publish_with_no_data(self, mock_pika):
        client = RabbitMQClient(rabbitmq_url="amqp://localhost")
        client.publish_event(
            routing_key="test.key",
            type=EventType.TEST_EVENT,
        )
        call_kwargs = mock_pika["publisher_channel"].basic_publish.call_args
        body = json.loads(call_kwargs.kwargs["body"])
        assert body["data"] == {}

    def test_publish_persistent_delivery_mode(self, mock_pika):
        client = RabbitMQClient(rabbitmq_url="amqp://localhost")
        client.publish_event(
            routing_key="test.key",
            type=EventType.TEST_EVENT,
            persistent=True,
        )
        props_call = mock_pika["pika"].BasicProperties.call_args
        assert props_call.kwargs["delivery_mode"] == 2

    def test_publish_non_persistent(self, mock_pika):
        client = RabbitMQClient(rabbitmq_url="amqp://localhost")
        client.publish_event(
            routing_key="test.key",
            type=EventType.TEST_EVENT,
            persistent=False,
        )
        props_call = mock_pika["pika"].BasicProperties.call_args
        assert props_call.kwargs["delivery_mode"] == 1


class TestConsumerRegistration:
    def test_register_consumers(self, mock_pika):
        client = RabbitMQClient(rabbitmq_url="amqp://localhost")

        def cb(ch, method, props, body):
            pass

        consumers = [
            Consumer(queue_name=Queue.Name.USER_EVENTS, callback=cb),
        ]
        client.register_consumers(consumers)
        assert len(client._consumers) == 1

    def test_identical_consumers_deduplicated(self, mock_pika):
        """Same queue + same callback reference = duplicate, only added once."""
        client = RabbitMQClient(rabbitmq_url="amqp://localhost")

        def cb(ch, method, props, body):
            pass

        consumers = [
            Consumer(queue_name=Queue.Name.USER_EVENTS, callback=cb),
            Consumer(queue_name=Queue.Name.USER_EVENTS, callback=cb),
        ]
        client.register_consumers(consumers)
        assert len(client._consumers) == 1

    def test_different_callbacks_same_queue_both_registered(self, mock_pika):
        """Same queue but different callbacks are treated as distinct consumers."""
        client = RabbitMQClient(rabbitmq_url="amqp://localhost")

        def cb1(ch, method, props, body):
            pass

        def cb2(ch, method, props, body):
            pass

        consumers = [
            Consumer(queue_name=Queue.Name.USER_EVENTS, callback=cb1),
            Consumer(queue_name=Queue.Name.USER_EVENTS, callback=cb2),
        ]
        client.register_consumers(consumers)
        assert len(client._consumers) == 2


class TestConnectionManagement:
    def test_close(self, mock_pika):
        client = RabbitMQClient(rabbitmq_url="amqp://localhost")
        client.close()
        mock_pika["connection"].close.assert_called_once()

    def test_close_already_closed(self, mock_pika):
        client = RabbitMQClient(rabbitmq_url="amqp://localhost")
        mock_pika["connection"].is_closed = True
        client.close()
        mock_pika["connection"].close.assert_not_called()

    def test_reconnects_on_closed_connection(self, mock_pika):
        client = RabbitMQClient(rabbitmq_url="amqp://localhost")

        mock_pika["connection"].is_closed = True
        new_conn = MagicMock()
        new_pub = MagicMock()
        new_con = MagicMock()
        new_conn.channel.side_effect = [new_pub, new_con]
        new_conn.is_closed = False
        mock_pika["pika"].BlockingConnection.return_value = new_conn

        client._ensure_connection()
        assert client.connection is new_conn


class TestSingleton:
    def test_get_client_creates_instance(self, mock_pika):
        c = get_client(rabbitmq_url="amqp://localhost", source="svc")
        assert c is not None
        assert isinstance(c, RabbitMQClient)

    def test_get_client_returns_same_instance(self, mock_pika):
        c1 = get_client(rabbitmq_url="amqp://localhost", source="svc")
        c2 = get_client(rabbitmq_url="amqp://localhost", source="svc")
        assert c1 is c2

    def test_close_client_resets_singleton(self, mock_pika):
        get_client(rabbitmq_url="amqp://localhost", source="svc")
        close_client()
        assert client_module._client is None
