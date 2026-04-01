from fastapi import APIRouter, HTTPException, Query
from database import database, locations, pallets, items
from models import LocationCreate, LocationOut
import sqlalchemy

router = APIRouter(prefix="/locations", tags=["locations"])


def make_label(row: str, slot: int, level: int, zone: str = "tent") -> str:
    if zone == "container":
        # row = "CON1A" → label = "CON1-A-1"
        # แปลง "CON1A" → container_no=1, row_letter=A
        import re
        m = re.match(r"CON(\d+)([A-Z]+)", row.upper())
        if m:
            return f"CON{m.group(1)}-{m.group(2)}-{slot}"
        return f"{row}-{slot}"
    return f"{row.upper()}-{slot:02d}-{level}"


@router.post("/", response_model=LocationOut)
async def create_location(data: LocationCreate):
    label = make_label(data.row, data.slot, data.level, data.zone)
    existing = await database.fetch_one(locations.select().where(locations.c.label == label))
    if existing:
        raise HTTPException(status_code=400, detail=f"Location {label} มีอยู่แล้ว")

    query = locations.insert().values(
        row=data.row.upper(),
        slot=data.slot,
        level=data.level,
        label=label,
        zone=data.zone,
        container_no=data.container_no,
    )
    new_id = await database.execute(query)
    return {"id": new_id, "row": data.row.upper(), "slot": data.slot,
            "level": data.level, "label": label, "zone": data.zone}


@router.get("/", response_model=list[LocationOut])
async def get_all_locations():
    return await database.fetch_all(
        locations.select().order_by(locations.c.row, locations.c.slot, locations.c.level)
    )


@router.get("/map")
async def get_map(zone: str = Query("tent", description="tent | container | all")):
    """
    ดู map ตาม zone
    - zone=tent     → เต้นท์ (default)
    - zone=container → ตู้คอนเทนเนอร์ทั้ง 3 ตู้
    - zone=all      → ทั้งหมด
    """
    if zone == "all":
        rows = await database.fetch_all(
            locations.select().order_by(locations.c.zone, locations.c.row, locations.c.slot, locations.c.level)
        )
    elif zone == "container":
        rows = await database.fetch_all(
            locations.select()
            .where(locations.c.zone == "container")
            .order_by(locations.c.row, locations.c.slot, locations.c.level)
        )
    else:
        rows = await database.fetch_all(
            locations.select()
            .where(sqlalchemy.or_(locations.c.zone == "tent", locations.c.zone == None))
            .order_by(locations.c.row, locations.c.slot, locations.c.level)
        )

    result = {}
    for loc in rows:
        row_key = loc["row"]
        if row_key not in result:
            result[row_key] = {}
        slot_key = str(loc["slot"])
        if slot_key not in result[row_key]:
            result[row_key][slot_key] = {}

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
            "zone": loc["zone"] or "tent",
        }

    return result


@router.get("/{location_id}", response_model=LocationOut)
async def get_location(location_id: int):
    row = await database.fetch_one(locations.select().where(locations.c.id == location_id))
    if not row:
        raise HTTPException(status_code=404, detail="ไม่พบตำแหน่งนี้")
    return row
