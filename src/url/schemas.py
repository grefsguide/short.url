from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List

class LinkCreate(BaseModel):
    original_url: str
    tag_name: str | None = Field(
        default=None,
        max_length=50,
        example="my-tag",
        description="Название проекта для группировки ссылок"
    )
    custom_alias: str | None = Field(
        default=None,
        min_length=4,
        max_length=20,
        pattern="^[a-zA-Z0-9_-]+$",
        example="my_custom_link",
        description="Пользовательский короткий код (допустимы буквы, цифры, '_' и '-')"
    )

class LinkUpdate(BaseModel):
    original_url: str
    tag_name: str = None

class LinkStats(BaseModel):
    original_url: str
    short_code: str
    tag_name: Optional[str] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None
    clicks: int
    expires_at: datetime

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class LinkSearchResult(BaseModel):
    short_code: str
    original_url: str
    tag_name: Optional[str] = None

    class Config:
        from_attributes = True
        extra = "ignore"

class ExpLinkResponse(BaseModel):
    message: Optional[str] = None
    data: Optional[List[LinkStats]] = None

