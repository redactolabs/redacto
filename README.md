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

### Version Management

To manage the package version:

```bash
# Check current version
uv version

# Bump version (patch, minor, or major)
uv version --bump patch
uv version --bump minor
uv version --bump major

# Set specific version
uv version 1.2.3

# Preview version change without writing
uv version --bump patch --dry-run
```

For releases, update the version using the commands above, then commit and push to trigger the automated build and tagging workflow.

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

#### Importing

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

## Using as a Dependency

To use this private package in other Poetry projects, you'll need to add it as a Git dependency and ensure proper authentication.

### 1. Add as Git Dependency

In the `pyproject.toml` of your consuming project, add the following to the `[tool.poetry.dependencies]` section:

```toml
redacto = { git = "https://github.com/redactolabs/redacto.git", rev = "main" }
```

You can also specify a specific `rev` (e.g., a tag like `v0.1.0` or a commit SHA) for more stable dependencies.

### 2. Configure Authentication

To allow Poetry to access your private GitHub repository, you'll need a GitHub Personal Access Token (PAT) with `repo` scope.

#### Using with Docker Compose

For projects using Docker Compose, you can pass the GitHub token as a build argument in your `docker-compose.yml`:

**docker-compose.yml example:**

```yaml
services:
  app:
    build:
      context: .
      dockerfile: docker/local/Dockerfile
      args:
        GITHUB_TOKEN: ${GITHUB_TOKEN}  # Pass from environment variable
```

**Dockerfile example:**

```dockerfile
FROM python:3.12 as base

# ... your existing setup ...

# Copy pyproject.toml and poetry.lock
COPY ./pyproject.toml ./poetry.lock ./

# ... poetry configuration ...

# Use build arg for GitHub token
ARG GITHUB_TOKEN

# Install dependencies with GitHub token
RUN GITHUB_TOKEN=$GITHUB_TOKEN poetry install --no-interaction --no-cache

# ... rest of your Dockerfile
```

**Usage:**

```bash
# Set the token in your environment
export GITHUB_TOKEN="your_github_personal_access_token"

# Build with docker-compose
docker-compose --profile app up --build
```

**Security Note:** The `GITHUB_TOKEN` is only used during the build process to install dependencies and is not stored in the final Docker image or available at runtime.
