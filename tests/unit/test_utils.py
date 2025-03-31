from src.auth.utils import hash_password, verify_password, create_access_token, decode_access_token
from src.config import SECRET_KEY
import jwt


def test_password_hashing():
    password = "secret"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_token():
    data = {"sub": "test_user"}
    token = create_access_token(data)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "test_user"


def test_invalid_token():
    invalid_token = jwt.encode({"sub": "user"}, "wrong_key", algorithm="HS256")
    assert decode_access_token(invalid_token) == {}