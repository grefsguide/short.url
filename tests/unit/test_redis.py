from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from src.main import app
from redis.exceptions import ConnectionError
import pytest
class FakeRedis:
    async def get(self, key):
        raise ConnectionError("Redis connection failed")

def test_redis_connection_error():
    with TestClient(app) as client:
        with patch("src.url.url.aioredis.from_url", lambda url: FakeRedis()):
            response = client.get("/api/links/test123")
            assert response.status_code == 500
            assert "Redis connection failed" in response.json()["detail"]

@pytest.mark.asyncio
@patch("src.url.url.redis_client.get")
async def test_redis_error(mock_redis, client):
    mock_redis.side_effect = ConnectionError("Redis error")
    response = client.get("/api/links/test123")
    assert response.status_code == 200