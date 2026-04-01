from fastapi import APIRouter, HTTPException
from database import database, movement_log, items
from models import MovementOut
import sqlalchemy

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/item/{item_id}", response_model=list[MovementOut])
async def get_item_history(item_id: int):
    """ดูประวัติการย้ายของสินค้าชิ้นนี้"""
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
async def get_recent_movements(limit: int = 20):
    """ดูการเคลื่อนย้ายล่าสุดทั้งหมด"""
    query = (
        sqlalchemy.select(
            movement_log.c.id,
            movement_log.c.item_id,
            items.c.item_name,
            items.c.item_code,
            movement_log.c.from_location_label,
            movement_log.c.to_location_label,
            movement_log.c.moved_by,
            movement_log.c.moved_at,
        )
        .select_from(movement_log.join(items, movement_log.c.item_id == items.c.id))
        .order_by(movement_log.c.moved_at.desc())
        .limit(limit)
    )
    return await database.fetch_all(query)
