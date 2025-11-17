import logging
from datetime import datetime, timezone
from typing import Callable, List
from uuid import uuid4

import pika
from cloudevents.http import CloudEvent, to_json
from pika.exceptions import AMQPChannelError

from .config import EXCHANGES_AND_QUEUES
from .events import ALL_EVENTS, EventType
from .exceptions import ConfigurationError, UnsupportedEventTypeError
from .models import Consumer, Exchange

pika_logger = logging.getLogger("pika")
pika_logger.setLevel(logging.CRITICAL)

_client = None


class RabbitMQClient:
    """
    RabbitMQ client for both publishing and consuming messages.
    """

    def __init__(
        self,
        rabbitmq_url: str,
        source: str | None = "undefined",
        logger: logging.Logger | None = None,
        heartbeat: int = 60,
        connection_attempts: int = 3,
        retry_delay: float = 5.0,
        prefetch_count: int = 1,
    ):
        """
        Initialize RabbitMQ client.

        Args:
            rabbitmq_url: RabbitMQ connection URL (required)
            logger: Logger instance
            source: Event source identifier (default: "undefined")
            heartbeat: Heartbeat interval in seconds (default: 60)
            connection_attempts: Number of connection attempts (default: 3)
            retry_delay: Delay between connection attempts (default: 5.0)
            prefetch_count: Prefetch count for consumer (default: 1)

        Raises:
            ConfigurationError: If rabbitmq_url is not provided
        """
        if not rabbitmq_url:
            raise ConfigurationError("rabbitmq_url is required")

        self.rabbitmq_url = rabbitmq_url
        self.heartbeat = heartbeat
        self.connection_attempts = connection_attempts
        self.retry_delay = retry_delay
        self.prefetch_count = prefetch_count

        self.logger = logger or logging.getLogger(__name__)
        self.source = source

        self.connection = None
        self.publisher_channel = None
        self.consumer_channel = None
        self._consumers = []
        self._setting_up = False

        self._setup_connection()

    def _setup_connection(self):
        """Setup RabbitMQ connection."""
        self._setting_up = True
        try:
            self.connection_params = pika.URLParameters(self.rabbitmq_url)
            self.connection_params.heartbeat = self.heartbeat
            self.connection_params.connection_attempts = self.connection_attempts
            self.connection_params.retry_delay = self.retry_delay

            self.connection = pika.BlockingConnection(self.connection_params)

            self.publisher_channel = self.connection.channel()
            self.consumer_channel = self.connection.channel()

            self.consumer_channel.basic_qos(prefetch_count=self.prefetch_count)

            self.setup_topology()

            self.logger.debug("RabbitMQ client initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize RabbitMQ client: {e}")
            raise
        finally:
            self._setting_up = False

    def _ensure_connection(self):
        """Ensure connection is alive and responsive, re-establish if necessary."""
        if self._setting_up:
            return

        if not self.connection or self.connection.is_closed:
            self.logger.warning(
                "RabbitMQ client connection lost, attempting to reconnect..."
            )
            self._setup_connection()
            return

        if not self.publisher_channel or not self.publisher_channel.is_open:
            self.logger.warning(
                "RabbitMQ client channel not available, attempting to reconnect..."
            )
            self._setup_connection()
            return

        try:
            self.connection.process_data_events(time_limit=0)
        except Exception as e:
            self.logger.warning(
                f"RabbitMQ connection is not responsive: {e}. Attempting to reconnect..."
            )
            self._setup_connection()
            return

    def _add_consumer(
        self,
        queue_name: str,
        callback: Callable,
        auto_ack: bool = True,
    ):
        """
        Add a consumer to the list of consumers to be registered on start_consuming.

        Args:
            queue_name: Name of the queue to consume from
            callback: Callback function to handle messages
            auto_ack: Whether to auto-acknowledge messages (default: True)
        """
        consumer = Consumer(
            queue_name=queue_name,
            callback=callback,
            auto_ack=auto_ack,
        )

        if consumer not in self._consumers:
            self._consumers.append(consumer)
            self.logger.debug(f"Added consumer for queue: {queue_name}")

    def setup_topology(self):
        """Set up RabbitMQ topology by declaring exchanges, queues, and bindings."""
        for exchange in EXCHANGES_AND_QUEUES:
            self.logger.debug(
                f"Declaring exchange: {exchange.name} (type: {exchange.type})"
            )
            self.declare_exchange(
                exchange_name=exchange.name,
                exchange_type=exchange.type,
                durable=exchange.durable,
                auto_delete=exchange.auto_delete,
            )

            for queue in exchange.queues:
                self.logger.debug(f"Declaring queue: {queue.name}")
                self.declare_queue(
                    queue_name=queue.name,
                    durable=queue.durable,
                    auto_delete=queue.auto_delete,
                    exclusive=queue.exclusive,
                )

                for binding in queue.bindings:
                    self.logger.debug(
                        f"Binding queue {queue.name} to exchange {exchange.name} with routing key '{binding.routing_key}'"
                    )
                    self.bind_queue(
                        queue_name=queue.name,
                        exchange_name=exchange.name,
                        routing_key=binding.routing_key,
                    )

    def declare_exchange(
        self,
        exchange_name: str,
        exchange_type: str = "direct",
        durable: bool = True,
        auto_delete: bool = False,
    ):
        """
        Declare an exchange.

        Args:
            exchange_name: Name of the exchange
            exchange_type: Type of exchange ('direct', 'topic', 'headers', 'fanout')
            durable: Whether exchange should survive broker restart
            auto_delete: Whether exchange should auto-delete when unused
        """
        self._ensure_connection()
        try:
            self.publisher_channel.exchange_declare(
                exchange=exchange_name,
                exchange_type=exchange_type,
                durable=durable,
                auto_delete=auto_delete,
            )
            self.logger.debug(
                f"Declared exchange: {exchange_name} (type: {exchange_type})"
            )
        except AMQPChannelError as e:
            self.logger.error(f"Failed to declare exchange {exchange_name}: {e}")
            raise

    def declare_queue(
        self,
        queue_name: str,
        durable: bool = True,
        auto_delete: bool = False,
        exclusive: bool = False,
    ):
        """
        Declare a queue.

        Args:
            queue_name: Name of the queue
            durable: Whether queue should survive broker restart
            auto_delete: Whether queue should auto-delete when unused
            exclusive: Whether queue should be exclusive to this connection

        Returns:
            Queue declaration result
        """
        self._ensure_connection()
        try:
            result = self.consumer_channel.queue_declare(
                queue=queue_name,
                durable=durable,
                auto_delete=auto_delete,
                exclusive=exclusive,
            )
            self.logger.debug(f"Declared queue: {queue_name}")
            return result
        except AMQPChannelError as e:
            self.logger.error(f"Failed to declare queue {queue_name}: {e}")
            raise

    def bind_queue(
        self,
        queue_name: str,
        exchange_name: str,
        routing_key: str,
    ):
        """
        Bind a queue to an exchange.

        Args:
            queue_name: Name of the queue
            exchange_name: Name of the exchange
            routing_key: Routing key for binding
        """
        self._ensure_connection()
        try:
            self.consumer_channel.queue_bind(
                queue=queue_name,
                exchange=exchange_name,
                routing_key=routing_key,
            )
            self.logger.debug(
                f"Bound queue {queue_name} to exchange {exchange_name} with routing key '{routing_key}'"
            )
        except AMQPChannelError as e:
            self.logger.error(
                f"Failed to bind queue {queue_name} to exchange {exchange_name}: {e}"
            )
            raise

    def register_consumers(self, consumers: List[Consumer]):
        """Register consumers for consuming messages."""
        for consumer in consumers:
            self.logger.debug(f"Registering consumer for queue: {consumer.queue_name}")
            self._add_consumer(
                queue_name=consumer.queue_name,
                callback=consumer.callback,
                auto_ack=consumer.auto_ack,
            )

    def start_consuming(self):
        """
        Start consuming messages from all registered queues. This method blocks and processes messages continuously.
        """
        self._ensure_connection()

        for consumer in self._consumers:
            try:
                self.consumer_channel.basic_consume(
                    queue=consumer.queue_name,
                    on_message_callback=consumer.callback,
                    auto_ack=consumer.auto_ack,
                )
                self.logger.debug(
                    f"Registered consumer for queue: {consumer.queue_name}"
                )
            except AMQPChannelError as e:
                self.logger.error(
                    f"Failed to register consumer for queue {consumer.queue_name}: {e}"
                )
                raise

        self.logger.debug("Starting to consume messages from all registered queues")
        self.consumer_channel.start_consuming()

    def close(self):
        """Close the RabbitMQ connection."""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                self.logger.debug("RabbitMQ client connection closed")
        except Exception as e:
            self.logger.error(f"Error closing RabbitMQ client connection: {e}")

    def publish_event(
        self,
        routing_key: str,
        type: EventType,
        data: dict = None,
        exchange_name: Exchange.Name = Exchange.Name.PLATFORM_EVENTS,
        persistent: bool = True,
    ):
        """
        Publish an event as a CloudEvent following CloudEvents spec v1.0.
        All required CloudEvent attributes are automatically set.

        Args:
            routing_key: Routing key for the message
            type: Event type (required by spec)
            data: Event data payload (optional)
            exchange_name: Name of the exchange to publish to (default: PLATFORM_EVENTS)
            persistent: Whether message should be persistent
        """
        if type not in ALL_EVENTS:
            raise UnsupportedEventTypeError(f"Unsupported event type: {type}")

        self._ensure_connection()
        try:
            attributes = {
                "specversion": "1.0",
                "type": str(type),
                "source": self.source,
                "id": str(uuid4()),
                "time": datetime.now(timezone.utc).isoformat(),
                "datacontenttype": "application/json",
            }

            event = CloudEvent(attributes=attributes, data=data or {})
            body = to_json(event)

            properties = pika.BasicProperties(
                delivery_mode=2 if persistent else 1,
                message_id=event["id"],
                content_type="application/cloudevents+json",
            )

            self.publisher_channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=body,
                properties=properties,
            )

            self.logger.debug(
                f"Published event to exchange '{exchange_name}' with routing key '{routing_key}' (type={type}, id={event.get('id')})"
            )
        except AMQPChannelError as e:
            self.logger.error(
                f"Failed to publish event to exchange {exchange_name}: {e}"
            )
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error publishing event: {e}")
            raise


def get_client(
    rabbitmq_url: str,
    source: str | None,
    logger: logging.Logger | None = None,
    heartbeat: int = 60,
    connection_attempts: int = 3,
    retry_delay: float = 5.0,
    prefetch_count: int = 1,
) -> RabbitMQClient:
    """
    Get the global singleton RabbitMQClient instance.

    This ensures that only one RabbitMQ connection exists throughout the application,
    which can be shared across multiple EventsSDK instances and consumers.

    Args:
        rabbitmq_url: RabbitMQ connection URL (required)
        logger: Logger instance (default: creates logger from __name__)
        source: Event source identifier (default: "undefined")
        heartbeat: Heartbeat interval in seconds (default: 60)
        connection_attempts: Number of connection attempts (default: 3)
        retry_delay: Delay between connection attempts (default: 5.0)
        prefetch_count: Prefetch count for consumer (default: 1)

    Returns:
        The global RabbitMQClient singleton instance

    Raises:
        ConfigurationError: If rabbitmq_url is not provided
    """
    global _client

    if logger is None:
        logger = logging.getLogger(__name__)

    if _client is None:
        _client = RabbitMQClient(
            rabbitmq_url=rabbitmq_url,
            heartbeat=heartbeat,
            connection_attempts=connection_attempts,
            retry_delay=retry_delay,
            prefetch_count=prefetch_count,
            logger=logger,
            source=source,
        )

    return _client


def close_client():
    """Close the global RabbitMQ client connection."""
    global _client

    if _client is not None:
        _client.close()
        _client = None
