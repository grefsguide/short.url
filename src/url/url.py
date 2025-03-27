from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, status, Query
from fastapi.responses import RedirectResponse
import datetime, secrets, re
import redis.asyncio as aioredis
from sqlalchemy import func
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
import urllib.parse

from src.config import TTL_LINK
from src.database import get_db
from src.url.models import Link, Tag
from src.url.schemas import LinkCreate, LinkUpdate, LinkStats, LinkSearchResult, ExpLinkResponse
from src.auth.auth import get_current_user

router = APIRouter()

#Написал по приколу, чтобы у юзера отображалось как bit.ly в /shorten и обновлении ссылки
BASE_SHORT_URL = "https://url.short/"

def generate_short_code(length: int = 8) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

async def get_redis():
    from src.config import REDIS_URL
    redis = await aioredis.from_url(REDIS_URL)
    try:
        yield redis
    finally:
        await redis.close()

@router.post("/links/shorten", status_code=status.HTTP_201_CREATED)
async def create_short_link(
                            link_data: LinkCreate,
                            background_tasks: BackgroundTasks,
                            request: Request,
                            db: Session = Depends(get_db),
                            current_user: dict = Depends(get_current_user),
                            redis=Depends(get_redis)
                            ):
    tag_id = None

    if link_data.tag_name:
        tag_name = link_data.tag_name.strip()

        tag = db.query(Tag).filter(
            func.lower(Tag.name) == func.lower(tag_name)
        ).first()

        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            try:
                db.commit()
                db.refresh(tag)
            except IntegrityError:
                db.rollback()
                tag = db.query(Tag).filter(
                    func.lower(Tag.name) == func.lower(tag_name)
                ).first()

        tag_id = tag.id

    if link_data.custom_alias:
        short_code = link_data.custom_alias.strip()

        if not re.fullmatch(r"^[a-zA-Z0-9_-]+$", short_code):
            raise HTTPException(
                status_code=422,
                detail="Недопустимые символы в коде. Разрешены: буквы, цифры, '_' и '-'"
            )

        if len(short_code) < 4 or len(short_code) > 20:
            raise HTTPException(
                status_code=400,
                detail="Длина кода должна быть от 4 до 20 символов"
            )

        if db.query(Link).filter(Link.short_code == short_code).first():
            raise HTTPException(
                status_code=400,
                detail="Ошибка, попробуйте другой код"
            )
    else:
        short_code = generate_short_code()
        while db.query(Link).filter(Link.short_code == short_code).first():
            short_code = generate_short_code()

    expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=TTL_LINK)

    owner_id = None if current_user.get("sub") == "anonymous" else current_user.get("sub")

    new_link = Link(
        original_url=urllib.parse.unquote(link_data.original_url),
        short_code=short_code,
        expires_at=expires_at,
        owner_id=owner_id,
        tag_id=tag_id
    )
    db.add(new_link)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Произошла ошибка при создании ссылки. Возможно такой код уже существует"
        )

    return {"short_url": BASE_SHORT_URL + new_link.short_code,
            "original_url": new_link.original_url}

@router.get("/links/search", response_model=list[LinkSearchResult])
async def search_links(
                       original_url: Optional[str] = Query(default=""),
                       tag_name: Optional[str] = Query(None),
                       db: Session = Depends(get_db)
                      ):
    query = db.query(Link).options(joinedload(Link.tag))

    if tag_name:
        tag_name_clean = tag_name.strip().lower()
        query = query.join(Tag).filter(func.lower(Tag.name) == tag_name_clean)


    if original_url:
        search_clean = urllib.parse.unquote(original_url).strip().lower()
        query = query.filter(func.lower(Link.original_url).ilike(f"%{search_clean}%"))


    links = query.order_by(Link.created_at.desc()).all()

    if not links:
        raise HTTPException(
                            status_code=404,
                            detail="Ссылки не найдены"
                            )

    return [
        LinkSearchResult(
                         original_url=link.original_url,
                         short_code=link.short_code,
                         tag_name=link.tag.name if link.tag else None
        ) for link in links
    ]

@router.get("/links/exp_links", response_model=ExpLinkResponse)
async def get_exp_links(
                        db: Session = Depends(get_db),
                        current_user: dict = Depends(get_current_user)
                       ):
    user_id = current_user.get("sub")
    if user_id == "anonymous":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация"
        )
    links = db.query(Link) \
        .options(joinedload(Link.tag)) \
        .filter(
                Link.owner_id == user_id,
                Link.is_active == False
               ) \
        .order_by(Link.expires_at.desc()) \
        .all()

    if not links:
        return {"message": "Нет недействительных ссылок"}

    return {
        "data": [
        LinkStats(
            short_code=link.short_code,
            original_url=link.original_url,
            tag_name=link.tag.name if link.tag else None,
            created_at=link.created_at,
            last_used_at=link.last_used_at,
            clicks=link.clicks,
            expires_at=link.expires_at
        ) for link in links
    ]}

@router.get("/links/{short_code}")
async def redirect_link(
                        short_code: str,
                        background_tasks: BackgroundTasks,
                        db: Session = Depends(get_db),
                        redis=Depends(get_redis)
                        ):
    cached_url = await redis.get(f"short:{short_code}")
    if cached_url:
        return RedirectResponse(url=cached_url.decode("utf-8"))

    link = db.query(Link).filter(
                                 Link.short_code == short_code,  # Теперь ищем по short_code
                                 Link.is_active == True
                                ).first()

    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")

    if link.expires_at and datetime.datetime.utcnow() > link.expires_at:
        link.is_active = False
        db.commit()
        raise HTTPException(status_code=410, detail="Ссылка истекла")

    link.clicks += 1
    link.last_used_at = datetime.datetime.utcnow()
    db.commit()

    await redis.set(f"short:{short_code}", link.original_url, ex=300)

    return RedirectResponse(
                            url=link.original_url,
                            status_code=status.HTTP_307_TEMPORARY_REDIRECT
                            )


@router.put("/links/{short_code}")
async def update_link(
                      short_code: str,
                      link_update: LinkUpdate,
                      db: Session = Depends(get_db),
                      current_user: dict = Depends(get_current_user),
                      redis=Depends(get_redis)
                      ):

    link = db.query(Link).filter(Link.short_code == short_code,
                                 Link.owner_id == current_user.get("sub")).first()

    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена или доступ запрещён")

    if link_update.original_url:
        link.original_url = link_update.original_url

    new_tag_id = None
    if link_update.tag_name is not None:
        if link_update.tag_name.strip() == "":
            new_tag_id = None
        else:
            tag_name = link_update.tag_name.strip()
            tag = db.query(Tag).filter(
                func.lower(Tag.name) == func.lower(tag_name)
            ).first()

            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.commit()
                db.refresh(tag)

            new_tag_id = tag.id
        link.tag_id = new_tag_id

    link.expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=TTL_LINK)

    db.commit()

    await redis.delete(f"short:{short_code}")

    return {
            "message": "Ссылка обновлена",
            "short_url": BASE_SHORT_URL + short_code,
            "original_url": urllib.parse.unquote(link.original_url),
            "expires_at": link.expires_at.isoformat()
            }


@router.delete("/links/{short_code}")
async def delete_link(
                      short_code: str,
                      db: Session = Depends(get_db),
                      current_user: dict = Depends(get_current_user),
                      redis=Depends(get_redis)
                      ):
    if current_user.get("sub") == str(2):
        raise HTTPException(status_code=401,
                            detail="Требуется аутентификация для удаления ссылки")

    link = db.query(Link).filter(Link.short_code == short_code,
                                 Link.owner_id == current_user.get("sub")).first()
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена или доступ запрещён")

    tag_name = link.tag.name if link.tag else ""
    
    db.delete(link)
    db.commit()

    await redis.hset(
        f"short:{short_code}",
        mapping={
            "url": link.original_url,
            "tag": tag_name
        }
    )
    return {"message": "Ссылка удалена"}


@router.get("/links/{short_code}/stats", response_model=LinkStats)
async def get_link_stats(
                          short_code: str,
                          db: Session = Depends(get_db)
                        ):
    link = db.query(Link).options(joinedload(Link.tag)) \
           .filter(Link.short_code == short_code) \
           .first()

    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    return LinkStats(
        short_code=link.short_code,
        original_url=link.original_url,
        tag_name=link.tag.name if link.tag else None,
        created_at=link.created_at,
        last_used_at=link.last_used_at,
        clicks=link.clicks,
        expires_at=link.expires_at
    )
