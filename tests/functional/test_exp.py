import uuid
from src.auth.models import User
from src.url.models import Link, Tag
from src.auth.utils import hash_password
from datetime import datetime, timedelta


def test_get_exp_links(client, db):
    test_data = {
        "original_url": "https://example.com",
        "short_code": "test123",
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=7),
        "clicks": 5,
        "is_active": True
    }

    link = Link(**test_data)
    db.add(link)
    db.commit()

    response = client.get(f"/api/links/{link.short_code}/stats")

    assert response.status_code == 200
    data = response.json()
    assert all(key in data for key in [
        "original_url",
        "short_code",
        "created_at",
        "expires_at",
        "clicks"
    ])

def test_exp_links_empty(client):

    email = f"empty_{uuid.uuid4()}@test.com"
    client.post("/auth/register", json={
        "email": email,
        "password": "pass"
    })


    client.post("/auth/login", json={
        "email": email,
        "password": "pass"
    })


    response = client.get("/api/links/exp_links")
    assert response.status_code == 200
    assert response.json()["message"] == "Нет недействительных ссылок"