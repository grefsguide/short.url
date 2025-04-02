import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from redis.exceptions import ConnectionError
from src.main import app
from src.url.url import generate_short_code

client = TestClient(app)

@pytest.mark.asyncio
async def test_redis_connection_error():
    with patch("src.url.url.aioredis.from_url", new_callable=AsyncMock) as mock_from_url:
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=ConnectionError("Redis connection failed"))
        mock_from_url.return_value = mock_redis

        with pytest.raises(ConnectionError):
            client.get("/api/links/test123")

@pytest.mark.asyncio
async def test_redis_cache_update_on_delete():
    with patch("src.url.url.aioredis.from_url", new_callable=AsyncMock) as mock_from_url:
        mock_redis = AsyncMock()
        mock_redis.hset = AsyncMock()
        mock_from_url.return_value = mock_redis

        register_response = client.post(
            "/auth/register",
            json={"email": "deleter@test.com", "password": "pass"}
        )
        login_response = client.post(
            "/auth/login",
            json={"email": "deleter@test.com", "password": "pass"}
        )
        token = login_response.cookies.get("access_token")

        unique_alias = "test_del_" + generate_short_code()
        create_response = client.post(
            "/api/links/shorten",
            json={"original_url": "https://redis-cache.com", "custom_alias": unique_alias},
            cookies={"access_token": token}
        )

        assert create_response.status_code == 201

        delete_response = client.delete(
            f"/api/links/{unique_alias}",
            cookies={"access_token": token}
        )
        assert delete_response.status_code == 200

        mock_redis.hset.assert_awaited_once()

def test_create_link_with_redis_mock():
    with patch("src.url.url.aioredis.from_url", new_callable=AsyncMock) as mock_from_url:
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis

        response = client.post(
            "/api/links/shorten",
            json={"original_url": "https://example.com", "custom_alias": None}
        )
        assert response.status_code == 201
        data = response.json()
        assert "short_url" in data
