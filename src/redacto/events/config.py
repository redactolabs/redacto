from typing import List

from .client import RabbitMQClient
from .models import Exchange, ExchangeType, Queue, QueueBinding, Subscriber

EXCHANGES_AND_QUEUES = [
    Exchange(
        name=Exchange.Name.PLATFORM_EVENTS,
        type=ExchangeType.TOPIC,
        queues=[
            Queue(
                name=Queue.Name.USER_EVENTS,
                bindings=[
                    QueueBinding(routing_key="vrm.#"),
                ],
            ),
            Queue(
                name=Queue.Name.VRM_EVENTS,
                bindings=[
                    QueueBinding(routing_key="vrm.#"),
                    QueueBinding(routing_key="platform.documents.#"),
                ],
            ),
        ],
    ),
]


def setup_topology(client: RabbitMQClient):
    for exchange in EXCHANGES_AND_QUEUES:
        client.logger.debug(
            f"Declaring exchange: {exchange.name} (type: {exchange.type})"
        )
        client.declare_exchange(
            exchange_name=exchange.name,
            exchange_type=exchange.type,
            durable=exchange.durable,
            auto_delete=exchange.auto_delete,
        )

        for queue in exchange.queues:
            client.logger.debug(f"Declaring queue: {queue.name}")
            client.declare_queue(
                queue_name=queue.name,
                durable=queue.durable,
                auto_delete=queue.auto_delete,
                exclusive=queue.exclusive,
            )

            for binding in queue.bindings:
                client.logger.debug(
                    f"Binding queue {queue.name} to exchange {exchange.name} with routing key '{binding.routing_key}'"
                )
                client.bind_queue(
                    queue_name=queue.name,
                    exchange_name=exchange.name,
                    routing_key=binding.routing_key,
                )


def register_subscribers(client: RabbitMQClient, subscribers: List[Subscriber]):
    for subscriber in subscribers:
        client.logger.debug(
            f"Registering subscriber for queue: {subscriber.queue_name}"
        )
        client.add_consumer(
            queue_name=subscriber.queue_name,
            callback=subscriber.callback,
        )
