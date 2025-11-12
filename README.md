# Redacto

Redacto platform package. For internal use only.

## Overview

This package provides shared functionality for the Redacto platform, including:

- **Events SDK** - Pub/sub messaging with RabbitMQ and CloudEvents

## Installation

```bash
uv sync
```

This will install dependencies and the package in editable mode. To sync dependencies without installing the project:

```bash
uv sync --no-install-project
```

## Development Setup

This package uses `uv` for dependency management and building.

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) installed

### Building

To build distribution files (wheels and source distributions):

```bash
uv build
```

This will create distribution files in the `dist/` directory.

**Note:** `uv sync` and `uv run` will automatically build/install the package when needed. To skip building during these commands, use the `--no-build` flag (though this may prevent installation in editable mode).

## Modules

### Events SDK

A Python SDK for pub/sub messaging using RabbitMQ and CloudEvents.

#### Features

- RabbitMQ pub/sub messaging
- CloudEvents v1.0 specification compliance
- Configurable connection parameters
- Automatic reconnection
- Type-safe event definitions
- Flexible topology configuration

#### Installation

After installing the `redacto` package, you can import the Events SDK:

```python
from redacto.events import RabbitMQClient, EventType, ConfigurationError, UnsupportedEventTypeError
```

#### Usage

##### Basic Client Setup

```python
import logging
from redacto.events import ConfigurationError, RabbitMQClient, EventType, UnsupportedEventTypeError

# Create a logger
logger = logging.getLogger(__name__)

# Create RabbitMQ client (rabbitmq_url is required)
# Raises ConfigurationError if rabbitmq_url is not provided
client = RabbitMQClient(
    rabbitmq_url="amqp://localhost",
    logger=logger,
    source="https://api.myapp.com",  # Any string identifier for your service
)

# Publish an event (raises UnsupportedEventTypeError for invalid event types from client)
try:
    client.publish_event(
        routing_key="user.created",
        type=EventType.TEST_EVENT,  # Must be one of the supported EventType enums
        data={"user_id": 123, "email": "user@example.com"}
    )
except UnsupportedEventTypeError as e:
    print(f"Invalid event type: {e}")
```

##### Advanced Usage

```python
# Setup topology (exchanges and queues)
from redacto.events import RabbitMQClient
from redacto.events.config import setup_topology, register_subscribers
from redacto.events.models import Subscriber, Queue

client = RabbitMQClient(rabbitmq_url="amqp://localhost")
setup_topology(client)

# Register subscribers

def my_callback(channel, method, properties, body):
    print("Received message:", body)

subscribers = [
    Subscriber(queue_name=Queue.Name.USER_EVENTS, callback=my_callback)
]
register_subscribers(client, subscribers)

# Start consuming
client.start_consuming()
```

**Note:** For application-specific SDKs with validation, create your own EventsSDK class that wraps RabbitMQClient with your supported event types and singleton management.

## Publishing to GitHub Package Registry

### 1. Configure Authentication

Create a GitHub Personal Access Token (PAT) with `write:packages` and `read:packages` scopes.

### 2. Update pyproject.toml

Update the `[tool.uv]` section in `pyproject.toml` with your GitHub organization/username:

```toml
[tool.uv]
publish-url = "https://pypi.pkg.github.com/OWNER"
```

Replace `OWNER` with your GitHub username or organization name.

### 3. Configure Authentication

Set up authentication using one of these methods:

**Option A: Using .env file (Recommended)**

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit `.env` and fill in your GitHub credentials:

```bash
GITHUB_USERNAME=your-github-username-or-org
GITHUB_TOKEN=your-github-token
```

3. Load the environment variables and publish:

```bash
export $(cat .env | xargs)
uv build
uv publish
```

**Option B: Using environment variables directly**

```bash
export UV_PUBLISH_USERNAME=your-github-username
export UV_PUBLISH_PASSWORD=your-github-token
uv publish
```

**Option C: Using uv's credential store**

```bash
uv publish --repository https://pypi.pkg.github.com/OWNER --username your-username --password your-token
```

### 4. Build and Publish

```bash
uv build
uv publish
```

## Using in Poetry Projects

To use this package in repositories that use Poetry, add the following to their `pyproject.toml`:

```toml
[[tool.poetry.source]]
name = "github"
url = "https://pypi.pkg.github.com/OWNER/simple"
default = false
secondary = true

[tool.poetry.dependencies]
redacto = { version = "^0.1.0", source = "github" }
```

And configure authentication in Poetry:

```bash
poetry config http-basic.github your-username your-token
```

Replace `OWNER` with your GitHub username or organization name.
