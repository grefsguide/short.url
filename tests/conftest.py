import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os
import uuid
from src.auth.utils import hash_password
from unittest.mock import AsyncMock
from src.url.models import Link, Tag

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from src.main import app
from src.database import Base, get_db
from src.auth.models import User
from src.url.models import Link, Tag

TEST_DATABASE_URL = "postgresql://admin:777@localhost:5432/test"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def clean_tables(db):
    db.execute(text("TRUNCATE users, links, tags RESTART IDENTITY CASCADE"))
    db.commit()

@pytest.fixture(autouse=True)
def setup_test_data(db):
    user = User(email="test@example.com", hashed_password=hash_password("secret"))
    tag = Tag(name="test-tag")
    links = [
        Link(original_url="https://active.com", short_code="active1", is_active=True),
        Link(original_url="https://inactive.com", short_code="inactive1", is_active=False)
    ]
    db.add_all([user, tag] + links)
    db.commit()
    yield
    db.rollback()

@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="module")
def test_data(db):
    user = User(email="testuser@example.com", hashed_password=hash_password("pass"))
    tag = Tag(name="test-tag")
    links = [
        Link(original_url="https://test1.com", short_code="test1", tag=tag),
        Link(original_url="https://test2.com", short_code="test2", is_active=False)
    ]
    db.add_all([user, tag] + links)
    db.commit()
    yield

@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def redis_mock(mocker):
    mock = AsyncMock()
    mocker.patch("src.url.url.redis", new=mock)
    return mock
@pytest.fixture
def authorized_client(client):
    client.post("/auth/register", json={"email": "user@test.com", "password": "pass"})
    client.post("/auth/login", json={"email": "user@test.com", "password": "pass"})
    return client



