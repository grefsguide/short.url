from fastapi import APIRouter, HTTPException, Depends, Response, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta
from src.config import TTL
from src.database import get_db
from src.auth.models import get_user_by_email, create_user
from src.auth.schemas import UserCreate, UserResponse
from src.auth.utils import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    if not token:
        token = request.cookies.get("access_token")
    if not token:
        anon = get_user_by_email(db, "anonymous@example.com")
        if not anon:
            anon = create_user(db, "anonymous@example.com", hash_password("anonymous"))
        return {"sub": None}
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или отсутствующий токен",
        )
    return payload

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    hashed_password = hash_password(user.password)
    new_user = create_user(db, user.email, hashed_password)
    return new_user

@router.post("/login", response_model=UserResponse)
def login(user: UserCreate, response: Response, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Неверные учетные данные")
    access_token = create_access_token(
        data={"sub": str(db_user.id)}, expires_delta=timedelta(minutes=TTL)
    )
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return db_user

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Вы вышли из системы, однако вы можете продолжать пользоваться сервисом в анонимном режиме."}

