# Oxia Testcontainer for Python

A [Testcontainers](https://testcontainers-python.readthedocs.io/) module for running [Oxia](https://github.com/streamnative/oxia) in integration tests.

## Installation

```bash
pip install testcontainers-oxia
```

## Usage

```python
from oxia_testcontainer import OxiaContainer

with OxiaContainer() as container:
    address = container.get_service_address()
    print(f"Oxia is running at {address}")

    # Use the Oxia CLI inside the container
    exit_code, output = container.exec(
        ["oxia", "client", "put", "hello", "world"]
    )
```

## Configuration

| Parameter   | Default             | Description                    |
|-------------|---------------------|--------------------------------|
| `image`     | `oxia/oxia:latest`  | Docker image to use            |
| `log_level` | `info`              | Oxia log level                 |
| `shards`    | `1`                 | Number of shards               |

## Methods

- `get_service_address()` - Returns `host:port` for the Oxia service (port 6648)
- `get_internal_address()` - Returns `host:port` for the internal port (port 6649)
- `get_metrics_url()` - Returns the full URL for the metrics endpoint (port 8080)

## Running Tests

```bash
pip install -e . && pip install pytest
pytest tests/
```

## License

Apache License 2.0
