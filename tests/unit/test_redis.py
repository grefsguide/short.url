from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from src.main import app
from redis.exceptions import ConnectionError
import pytest

class FakeRedis:
    async def get(self, key):
        raise ConnectionError("Redis connection failed")

@pytest.mark.asyncio
async def test_redis_connection_error():
    with patch("src.url.url.aioredis.from_url") as mock_redis:
        mock_redis.return_value = AsyncMock()
        mock_redis.return_value.get.side_effect = ConnectionError("Redis connection failed")

        with TestClient(app) as client:
            response = client.get("/api/links/test123")
            assert response.status_code == 200

@pytest.mark.asyncio
@patch("src.url.url.redis_client.get")
async def test_redis_error(mock_redis, client):
    mock_redis.side_effect = ConnectionError("Redis error")
    response = client.get("/api/links/test123")
    assert response.status_code == 200