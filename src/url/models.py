from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from src.database import Base, engine, SessionLocal


class Link(Base):
    __tablename__ = "links"
    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, nullable=False)
    short_code = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=func.now())
    last_used_at = Column(DateTime, nullable=True)
    clicks = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=True)

    owner = relationship("User", back_populates="links")
    tag = relationship("Tag", back_populates="links")

    user = relationship("User", back_populates="links", overlaps="owner")

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    links = relationship("Link", back_populates="tag")

Base.metadata.create_all(bind=engine)