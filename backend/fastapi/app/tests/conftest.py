from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from app.main import app

from unittest.mock import AsyncMock

@pytest.fixture(scope="module")
def mock_redis():
    mock = AsyncMock()
    return mock

@pytest.fixture(scope="module")
def client(mock_redis) -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        app.state.redis.xadd = mock_redis
        yield c