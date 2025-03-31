import pytest
from fastapi import HTTPException
import datetime
from src.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)
from src.config import SECRET_KEY

def test_password_hashing_consistency():
    plain = "secret123"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed)

def test_token_lifecycle():
    payload = {"sub": "user123"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "user123"

def test_expired_token():
    expired_token = create_access_token(
        data={"sub": "user1"},
        expires_delta=datetime.timedelta(minutes=-5)
    )
    assert decode_access_token(expired_token) == {}

def test_invalid_token_format():
    assert decode_access_token("invalid.token.here") == {}