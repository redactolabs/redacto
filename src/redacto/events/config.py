from .models import Exchange, ExchangeType, Queue, QueueBinding

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
