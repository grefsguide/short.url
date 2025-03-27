from sqlalchemy import Column, Integer, String
from src.database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String)

    links = relationship("Link", back_populates="owner", cascade="all, delete-orphan")

def get_user_by_email(db, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db, email: str, hashed_password: str):
    new_user = User(email=email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user