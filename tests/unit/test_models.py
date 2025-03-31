import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from src.auth.models import User
from src.url.models import Link, Tag
import uuid

def test_user_model(db):
    email = f"test_{uuid.uuid4()}@example.com"

    user = User(email=email, hashed_password="secret")
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.id is not None
    assert db.query(User).filter(User.email == email).first() == user


def test_link_model(db):
    try:
        user = User(email=f"user_{uuid.uuid4()}@example.com", hashed_password="pass")
        link = Link(original_url="https://example.com", short_code="ex123")
        user.links.append(link)
        db.add(user)
        db.commit()

        assert link.id is not None
    finally:
        db.rollback()


def test_tag_relationships(db):
    tag = Tag(name="important")
    link = Link(original_url="https://example.com", short_code="ex123", tag=tag)
    db.add_all([tag, link])
    db.commit()

    assert tag.links[0].short_code == "ex123"
    assert link.tag.name == "important"


def test_user_delete_cascades(db):
    user = User(email="cascade@test.com", hashed_password="pass")
    db.add(user)
    db.commit()

    link = Link(
        original_url="https://test.com",
        short_code="test",
        owner_id=user.id
    )
    db.add(link)
    db.commit()

    db.delete(user)
    db.commit()

    assert db.query(Link).filter(Link.id == link.id).count() == 0