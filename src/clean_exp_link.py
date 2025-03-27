import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.database import get_db
from src.url.models import Link
from src.config import TTL_LINK, CLEANUP_INTERVAL
import logging

logger = logging.getLogger(__name__)

async def cleanup_expired_links(loop_once: bool = False):
    while True:
        try:
            db: Session = next(get_db())
            now = datetime.utcnow()

            deactivate_query = db.query(Link).filter(
                and_(
                    Link.expires_at <= now,
                    Link.is_active == True
                )
            )
            deactivate_query.update({"is_active": False})

            delete_threshold = now - timedelta(days=TTL_LINK)
            delete_query = db.query(Link).filter(
                and_(
                    Link.expires_at <= delete_threshold,
                    Link.is_active == False
                )
            )
            delete_count = delete_query.delete()
            db.commit()
            logger.info(f"Очистка: Отключено {deactivate_query.count()}, Удалено {delete_count}")
        except Exception as e:
            db.rollback()
            logger.error(f"Cleanup error: {str(e)}")
        if loop_once:
            break
        await asyncio.sleep(CLEANUP_INTERVAL)