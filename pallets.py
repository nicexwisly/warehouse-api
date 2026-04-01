from fastapi import APIRouter, HTTPException
from database import database, pallets, locations, items
from models import PalletCreate, PalletOut
import sqlalchemy

router = APIRouter(prefix="/pallets", tags=["pallets"])


@router.post("/", response_model=PalletOut)
async def create_pallet(data: PalletCreate):
    # เช็คว่า location มีจริง
    loc = await database.fetch_one(
        locations.select().where(locations.c.id == data.location_id)
    )
    if not loc:
        raise HTTPException(status_code=404, detail="ไม่พบตำแหน่งนี้")

    # เช็ค pallet_code ซ้ำ
    existing = await database.fetch_one(
        pallets.select().where(pallets.c.pallet_code == data.pallet_code)
    )
    if existing:
        raise HTTPException(status_code=400, detail=f"Pallet code '{data.pallet_code}' มีอยู่แล้ว")

    query = pallets.insert().values(**data.model_dump())
    new_id = await database.execute(query)
    row = await database.fetch_one(pallets.select().where(pallets.c.id == new_id))
    return row


@router.get("/", response_model=list[PalletOut])
async def get_all_pallets():
    return await database.fetch_all(pallets.select().order_by(pallets.c.id))


@router.get("/{pallet_id}")
async def get_pallet_detail(pallet_id: int):
    """ดูพาเลทพร้อมตำแหน่งและรายการสินค้าทั้งหมด"""
    pallet = await database.fetch_one(
        pallets.select().where(pallets.c.id == pallet_id)
    )
    if not pallet:
        raise HTTPException(status_code=404, detail="ไม่พบพาเลทนี้")

    loc = await database.fetch_one(
        locations.select().where(locations.c.id == pallet["location_id"])
    )

    item_list = await database.fetch_all(
        items.select().where(items.c.pallet_id == pallet_id)
    )

    return {
        "pallet": dict(pallet),
        "location": dict(loc) if loc else None,
        "items": [dict(i) for i in item_list],
    }


@router.patch("/{pallet_id}/move")
async def move_pallet(pallet_id: int, location_id: int):
    """ย้ายพาเลททั้งใบไปตำแหน่งใหม่"""
    pallet = await database.fetch_one(pallets.select().where(pallets.c.id == pallet_id))
    if not pallet:
        raise HTTPException(status_code=404, detail="ไม่พบพาเลทนี้")

    loc = await database.fetch_one(locations.select().where(locations.c.id == location_id))
    if not loc:
        raise HTTPException(status_code=404, detail="ไม่พบตำแหน่งนี้")

    await database.execute(
        pallets.update().where(pallets.c.id == pallet_id).values(location_id=location_id)
    )
    return {"message": f"ย้ายพาเลท {pallet['pallet_code']} ไป {loc['label']} แล้ว"}
