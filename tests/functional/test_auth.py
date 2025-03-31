import uuid
from src.auth.utils import hash_password
from src.auth.models import User
from src.database import get_db

def test_register(client):
        email = f"test_{uuid.uuid4()}@example.com"
        response = client.post("/auth/register", json={
            "email": email,
            "password": "password"
        })
        assert response.status_code == 200

def test_double_register(client):
    client.post("/auth/register", json={
        "email": "duplicate@test.com",
        "password": "password"
    })

    response = client.post("/auth/register", json={
        "email": "duplicate@test.com",
        "password": "password"
    })
    assert response.status_code == 400
    assert "уже существует" in response.json()["detail"]

def test_login(client):

    email = f"test_{uuid.uuid4()}@example.com"
    password = "password"

    with client.app.dependency_overrides[get_db]() as session:
        user = User(email=email, hashed_password=hash_password(password))
        session.add(user)
        session.commit()

    response = client.post("/auth/login", json={
        "email": email,
        "password": password
    })
    assert response.status_code == 200

def test_logout(client):
    client.post("/auth/login", json={"email": "test@example.com", "password": "password"})
    response = client.post("/auth/logout")
    assert response.status_code == 200
    assert "access_token" not in response.cookies

def test_anonymous_access(client):
    response = client.post("/api/links/shorten", json={"original_url": "https://anon.com"})
    assert response.status_code == 201

def test_invalid_email_registration(client):
    response = client.post("/auth/register", json={
        "email": "invalid-email",
        "password": "pass"
    })
    assert response.status_code == 422
    assert "email" in response.text