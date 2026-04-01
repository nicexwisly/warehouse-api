from fastapi import APIRouter, HTTPException, Query
from database import database, items, pallets, locations, movement_log
from models import ItemCreate, ItemOut, ItemSearchResult, ItemMove
import sqlalchemy

router = APIRouter(prefix="/items", tags=["items"])


@router.post("/", response_model=ItemOut)
async def add_item(data: ItemCreate):
    # เช็คว่า pallet มีจริง
    pallet = await database.fetch_one(pallets.select().where(pallets.c.id == data.pallet_id))
    if not pallet:
        raise HTTPException(status_code=404, detail="ไม่พบพาเลทนี้")

    query = items.insert().values(**data.model_dump())
    new_id = await database.execute(query)
    row = await database.fetch_one(items.select().where(items.c.id == new_id))
    return row


@router.get("/search", response_model=list[ItemSearchResult])
async def search_items(q: str = Query(..., min_length=1, description="ค้นหาด้วยชื่อหรือรหัสสินค้า")):
    """ค้นหาสินค้า → แสดงว่าอยู่ที่ไหนในเต้นท์"""
    query = (
        sqlalchemy.select(
            items.c.id,
            items.c.item_code,
            items.c.item_name,
            items.c.qty,
            items.c.unit,
            pallets.c.pallet_code,
            locations.c.label.label("location_label"),
        )
        .select_from(
            items
            .join(pallets, items.c.pallet_id == pallets.c.id)
            .join(locations, pallets.c.location_id == locations.c.id)
        )
        .where(
            sqlalchemy.or_(
                items.c.item_name.ilike(f"%{q}%"),
                items.c.item_code.ilike(f"%{q}%"),
            )
        )
        .order_by(locations.c.label)
    )
    rows = await database.fetch_all(query)
    return rows


@router.get("/{item_id}", response_model=ItemOut)
async def get_item(item_id: int):
    row = await database.fetch_one(items.select().where(items.c.id == item_id))
    if not row:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้านี้")
    return row


@router.patch("/{item_id}/move")
async def move_item(item_id: int, data: ItemMove):
    """ย้ายสินค้าไปพาเลทอื่น พร้อมบันทึก movement log"""
    # เช็คสินค้า
    item = await database.fetch_one(items.select().where(items.c.id == item_id))
    if not item:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้านี้")

    # ตำแหน่งเดิม
    from_pallet = await database.fetch_one(pallets.select().where(pallets.c.id == item["pallet_id"]))
    from_loc = await database.fetch_one(locations.select().where(locations.c.id == from_pallet["location_id"]))

    # ตำแหน่งใหม่
    to_pallet = await database.fetch_one(pallets.select().where(pallets.c.id == data.to_pallet_id))
    if not to_pallet:
        raise HTTPException(status_code=404, detail="ไม่พบพาเลทปลายทาง")
    to_loc = await database.fetch_one(locations.select().where(locations.c.id == to_pallet["location_id"]))

    # บันทึก log ก่อนย้าย
    await database.execute(
        movement_log.insert().values(
            item_id=item_id,
            from_pallet_id=item["pallet_id"],
            to_pallet_id=data.to_pallet_id,
            from_location_label=from_loc["label"] if from_loc else None,
            to_location_label=to_loc["label"],
            moved_by=data.moved_by,
        )
    )

    # ย้ายสินค้า
    await database.execute(
        items.update().where(items.c.id == item_id).values(pallet_id=data.to_pallet_id)
    )

    return {
        "message": f"ย้ายสินค้า '{item['item_name']}' จาก {from_loc['label']} → {to_loc['label']} แล้ว"
    }


@router.delete("/{item_id}")
async def delete_item(item_id: int):
    item = await database.fetch_one(items.select().where(items.c.id == item_id))
    if not item:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้านี้")
    await database.execute(items.delete().where(items.c.id == item_id))
    return {"message": "ลบสินค้าแล้ว"}
