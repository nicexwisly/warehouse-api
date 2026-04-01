from fastapi import APIRouter, Query
import json
import os

router = APIRouter(prefix="/master", tags=["master"])

_items_cache: list[dict] = []
_barcode_index: dict[str, dict] = {}   # barcode → item (lookup O(1))


def load_master():
    global _items_cache, _barcode_index
    path = os.path.join(os.path.dirname(__file__), '..', 'items_master.json')
    if not os.path.exists(path):
        _items_cache = []
        return

    with open(path, encoding='utf-8') as f:
        _items_cache = json.load(f)

    # สร้าง barcode index
    _barcode_index = {}
    for item in _items_cache:
        for bc in item.get('barcodes', []):
            _barcode_index[str(bc)] = item


@router.get("/items")
async def search_master(q: str = Query(..., min_length=1), limit: int = 20):
    """
    ค้นหาสินค้าจาก master list
    รองรับ: ชื่อสินค้า, รหัสสินค้า, barcode
    """
    if not _items_cache:
        load_master()

    q_stripped = q.strip()

    # ถ้าเป็น barcode (ตัวเลขล้วน) → ค้นหาจาก barcode index ก่อนเลย O(1)
    if q_stripped.isdigit() and q_stripped in _barcode_index:
        item = _barcode_index[q_stripped]
        return [{"code": item["code"], "name": item["name"], "barcode": q_stripped}]

    # ค้นหาแบบ partial match จาก code, name, barcodes
    q_lower = q_stripped.lower()
    results = []

    for item in _items_cache:
        code = str(item.get("code", ""))
        name = str(item.get("name", ""))

        matched = q_lower in code.lower() or q_lower in name.lower()

        # เช็ค partial barcode ด้วย (กรณีพิมพ์ barcode ไม่ครบ)
        if not matched:
            for bc in item.get('barcodes', []):
                if q_stripped in str(bc):
                    matched = True
                    break

        if matched:
            results.append({
                "code": code,
                "name": name,
                "barcodes": item.get("barcodes", [])
            })
            if len(results) >= limit:
                break

    return results
