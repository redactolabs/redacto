from enum import Enum
from typing import Callable, List

from pydantic import BaseModel, Field


class ExchangeType(str, Enum):
    DIRECT = "direct"
    TOPIC = "topic"
    HEADERS = "headers"
    FANOUT = "fanout"

    def __str__(self):
        return self.value


class QueueBinding(BaseModel):
    routing_key: str


class Queue(BaseModel):
    class Name(str, Enum):
        USER_EVENTS = "user.events"
        VRM_EVENTS = "vrm.events"

        def __str__(self):
            return self.value

    name: Name
    durable: bool = True
    auto_delete: bool = False
    exclusive: bool = False
    bindings: List[QueueBinding] = Field(default_factory=list)


class Subscriber(BaseModel):
    queue_name: Queue.Name
    callback: Callable


class Exchange(BaseModel):
    class Name(str, Enum):
        PLATFORM_EVENTS = "platform.events"

        def __str__(self):
            return self.value

    name: Name
    type: ExchangeType = ExchangeType.TOPIC
    durable: bool = True
    auto_delete: bool = False
    queues: List[Queue] = Field(default_factory=list)
