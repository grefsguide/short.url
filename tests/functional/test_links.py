from urllib.request import Request
from src.url.models import Link, Tag
import pytest
import uuid
from datetime import datetime
from src.auth.auth import get_current_user, get_user_by_email, create_user
from src.auth.utils import hash_password

def test_create_link(client):

    client.post("/auth/register", json={"email": "user@test.com", "password": "pass"})
    login_res = client.post("/auth/login", json={"email": "user@test.com", "password": "pass"})
    token = login_res.cookies.get("access_token")


    response = client.post(
        "/api/links/shorten",
        json={"original_url": "https://example.com"},
        cookies={"access_token": token}
    )
    assert response.status_code == 201
    assert "short_url" in response.json()


def test_redirect_link(client):

    create_res = client.post("/api/links/shorten", json={f"original_url": "https://example.com"})
    short_code = create_res.json()["short_url"].split("/")[-1]


    response = client.get(f"/api/links/{short_code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com"

def test_update_nonexistent_link(client):
    response = client.put("/api/links/invalid123", json={
        "original_url": "https://new-url.com"
    })
    assert response.status_code == 404

def test_delete_link_unauthorized(client, db):
    email = f"test_{uuid.uuid4()}@example.com"
    client.post("/auth/register", json={"email": email, "password": "pass"})
    login_res = client.post("/auth/login", json={"email": email, "password": "pass"})
    token = login_res.cookies.get("access_token")

    client.post(
        "/api/links/shorten",
        json={"original_url": "https://example.com", "custom_alias": "test_delete"},
        cookies={"access_token": token}
    )

    response = client.delete("/api/links/test_delete", cookies= None)
    assert response.status_code == 401

def test_delete_link_not_found(authorized_client):
    response = authorized_client.delete("/api/links/nonexistent")
    assert response.status_code == 404

def test_create_link_with_invalid_alias(client):
    response = client.post("/api/links/shorten", json={
        "original_url": "https://test.com",
        "custom_alias": "inv@_+=-!&?@lid"
    })
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("custom_alias" in error["loc"] for error in errors)

def test_duplicate_alias(client):
    client.post("/api/links/shorten", json={
        "original_url": "https://a.com",
        "custom_alias": "myalias"
    })
    response = client.post("/api/links/shorten", json={
        "original_url": "https://b.com",
        "custom_alias": "myalias"
    })
    assert response.status_code == 400


def test_click_counter(client):
    create_res = client.post("/api/links/shorten", json={
        "original_url": "https://clicks.com"
    })
    short_code = create_res.json()["short_url"].split("/")[-1]

    client.get(f"/api/links/{short_code}")
    stats = client.get(f"/api/links/{short_code}/stats").json()
    assert stats["clicks"] == 1
