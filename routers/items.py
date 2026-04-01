from fastapi import APIRouter, HTTPException, Query
from database import database, items, pallets, locations, movement_log
from models import ItemCreate, ItemOut, ItemSearchResult, ItemMove, ItemDeduct
import sqlalchemy

router = APIRouter(prefix="/items", tags=["items"])


@router.post("/", response_model=ItemOut)
async def add_item(data: ItemCreate):
    pallet = await database.fetch_one(pallets.select().where(pallets.c.id == data.pallet_id))
    if not pallet:
        raise HTTPException(status_code=404, detail="ไม่พบพาเลทนี้")
    query = items.insert().values(**data.model_dump())
    new_id = await database.execute(query)
    row = await database.fetch_one(items.select().where(items.c.id == new_id))
    return row


@router.get("/search", response_model=list[ItemSearchResult])
async def search_items(q: str = Query(..., min_length=1)):
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
    return await database.fetch_all(query)


@router.get("/{item_id}", response_model=ItemOut)
async def get_item(item_id: int):
    row = await database.fetch_one(items.select().where(items.c.id == item_id))
    if not row:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้านี้")
    return row


@router.patch("/{item_id}/deduct")
async def deduct_item(item_id: int, data: ItemDeduct):
    """หยิบสินค้าออก — ตัดสต็อก พร้อมบันทึก log ว่าใครหยิบ"""
    item = await database.fetch_one(items.select().where(items.c.id == item_id))
    if not item:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้านี้")
    if data.qty <= 0:
        raise HTTPException(status_code=400, detail="จำนวนต้องมากกว่า 0")
    if data.qty > item["qty"]:
        raise HTTPException(status_code=400, detail=f"สต็อกมีแค่ {item['qty']} {item['unit'] or 'ชิ้น'}")

    pallet = await database.fetch_one(pallets.select().where(pallets.c.id == item["pallet_id"]))
    loc = await database.fetch_one(locations.select().where(locations.c.id == pallet["location_id"]))

    new_qty = item["qty"] - data.qty

    # บันทึก log
    await database.execute(
        movement_log.insert().values(
            item_id=item_id,
            from_pallet_id=pallet["id"],
            to_pallet_id=pallet["id"],
            from_location_label=loc["label"],
            to_location_label=loc["label"],
            action="deduct",
            qty_changed=data.qty,
            moved_by=data.actor_name,
            actor_user_id=data.actor_user_id,
        )
    )

    # ตัดสต็อก — ถ้าเหลือ 0 ให้ลบ item ออก
    if new_qty == 0:
        await database.execute(items.delete().where(items.c.id == item_id))
        return {"message": f"หยิบ '{item['item_name']}' ออกครบ ลบออกจากระบบแล้ว", "remaining": 0}
    else:
        await database.execute(items.update().where(items.c.id == item_id).values(qty=new_qty))
        return {"message": f"หยิบ '{item['item_name']}' {data.qty} {item['unit'] or 'ชิ้น'} แล้ว", "remaining": new_qty}


@router.patch("/{item_id}/move")
async def move_item(item_id: int, data: ItemMove):
    item = await database.fetch_one(items.select().where(items.c.id == item_id))
    if not item:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้านี้")
    from_pallet = await database.fetch_one(pallets.select().where(pallets.c.id == item["pallet_id"]))
    from_loc = await database.fetch_one(locations.select().where(locations.c.id == from_pallet["location_id"]))
    to_pallet = await database.fetch_one(pallets.select().where(pallets.c.id == data.to_pallet_id))
    if not to_pallet:
        raise HTTPException(status_code=404, detail="ไม่พบพาเลทปลายทาง")
    to_loc = await database.fetch_one(locations.select().where(locations.c.id == to_pallet["location_id"]))
    await database.execute(
        movement_log.insert().values(
            item_id=item_id,
            from_pallet_id=item["pallet_id"],
            to_pallet_id=data.to_pallet_id,
            from_location_label=from_loc["label"] if from_loc else None,
            to_location_label=to_loc["label"],
            action="move",
            moved_by=data.moved_by,
        )
    )
    await database.execute(items.update().where(items.c.id == item_id).values(pallet_id=data.to_pallet_id))
    return {"message": f"ย้ายสินค้า '{item['item_name']}' จาก {from_loc['label']} → {to_loc['label']} แล้ว"}


@router.delete("/{item_id}")
async def delete_item(item_id: int):
    item = await database.fetch_one(items.select().where(items.c.id == item_id))
    if not item:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้านี้")
    await database.execute(items.delete().where(items.c.id == item_id))
    return {"message": "ลบสินค้าแล้ว"}
