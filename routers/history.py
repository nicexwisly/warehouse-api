from fastapi import APIRouter, HTTPException
from database import database, movement_log, items
import sqlalchemy

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/item/{item_id}")
async def get_item_history(item_id: int):
    item = await database.fetch_one(items.select().where(items.c.id == item_id))
    if not item:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้านี้")
    rows = await database.fetch_all(
        movement_log.select()
        .where(movement_log.c.item_id == item_id)
        .order_by(movement_log.c.moved_at.desc())
    )
    return rows


@router.get("/recent")
async def get_recent_movements(limit: int = 50):
    """ดูประวัติล่าสุด พร้อมชื่อสินค้าและ action"""
    query = (
        sqlalchemy.select(
            movement_log.c.id,
            movement_log.c.item_id,
            items.c.item_name,
            items.c.item_code,
            items.c.unit,
            movement_log.c.action,
            movement_log.c.qty_changed,
            movement_log.c.from_location_label,
            movement_log.c.to_location_label,
            movement_log.c.moved_by,
            movement_log.c.actor_user_id,
            movement_log.c.moved_at,
        )
        .select_from(
            movement_log.outerjoin(items, movement_log.c.item_id == items.c.id)
        )
        .order_by(movement_log.c.moved_at.desc())
        .limit(limit)
    )
    return await database.fetch_all(query)
