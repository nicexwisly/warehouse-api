from fastapi import APIRouter, HTTPException
from database import database, locations, pallets, items
from models import LocationCreate, LocationOut
import sqlalchemy

router = APIRouter(prefix="/locations", tags=["locations"])


def make_label(row: str, slot: int, level: int) -> str:
    return f"{row.upper()}-{slot:02d}-{level}"


@router.post("/", response_model=LocationOut)
async def create_location(data: LocationCreate):
    label = make_label(data.row, data.slot, data.level)
    # เช็คซ้ำ
    existing = await database.fetch_one(
        locations.select().where(locations.c.label == label)
    )
    if existing:
        raise HTTPException(status_code=400, detail=f"Location {label} มีอยู่แล้ว")

    query = locations.insert().values(
        row=data.row.upper(),
        slot=data.slot,
        level=data.level,
        label=label,
    )
    new_id = await database.execute(query)
    return {**data.model_dump(), "id": new_id, "label": label}


@router.get("/", response_model=list[LocationOut])
async def get_all_locations():
    return await database.fetch_all(
        locations.select().order_by(locations.c.row, locations.c.slot, locations.c.level)
    )


@router.get("/map")
async def get_map():
    """ดูภาพรวม map เต้นท์ - จัดกลุ่มตามแถว/ล็อค/ชั้น พร้อมจำนวนสินค้า"""
    rows = await database.fetch_all(
        locations.select().order_by(locations.c.row, locations.c.slot, locations.c.level)
    )

    result = {}
    for loc in rows:
        row_key = loc["row"]
        if row_key not in result:
            result[row_key] = {}

        slot_key = str(loc["slot"])
        if slot_key not in result[row_key]:
            result[row_key][slot_key] = {}

        # นับสินค้าในตำแหน่งนี้
        count_query = (
            sqlalchemy.select(sqlalchemy.func.count(items.c.id))
            .select_from(items.join(pallets, items.c.pallet_id == pallets.c.id))
            .where(pallets.c.location_id == loc["id"])
        )
        item_count = await database.fetch_val(count_query)

        result[row_key][slot_key][str(loc["level"])] = {
            "location_id": loc["id"],
            "label": loc["label"],
            "item_count": item_count or 0,
        }

    return result


@router.get("/{location_id}", response_model=LocationOut)
async def get_location(location_id: int):
    row = await database.fetch_one(
        locations.select().where(locations.c.id == location_id)
    )
    if not row:
        raise HTTPException(status_code=404, detail="ไม่พบตำแหน่งนี้")
    return row
