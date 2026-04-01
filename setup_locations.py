"""
Setup Script: เพิ่มตำแหน่งและพาเลทเข้าระบบครั้งเดียว
-------------------------------------------------------
รัน: python setup_locations.py

จะสร้าง:
- 72 ตำแหน่ง (6 แถว x 4 ล็อค x 3 ชั้น)
- 72 พาเลท (P-001 ถึง P-072) แต่ละตำแหน่ง 1 พาเลท
"""

import requests

API_URL = "https://warehouse-api-njvm.onrender.com"  # ← แก้ให้ตรงกับ URL ของคุณ

ROWS  = ["A", "B", "C", "D", "E", "F"]
SLOTS = [1, 2, 3, 4]
LEVELS = [1, 2, 3]


def create_locations():
    print("📍 กำลังสร้างตำแหน่ง...")
    created, skipped = 0, 0
    location_map = {}  # label → id

    for row in ROWS:
        for slot in SLOTS:
            for level in LEVELS:
                label = f"{row}-{slot:02d}-{level}"
                res = requests.post(f"{API_URL}/locations", json={
                    "row": row, "slot": slot, "level": level
                })
                if res.status_code == 200:
                    data = res.json()
                    location_map[label] = data["id"]
                    print(f"  ✅ {label}")
                    created += 1
                elif res.status_code == 400:
                    # มีอยู่แล้ว ดึง id มา
                    all_locs = requests.get(f"{API_URL}/locations").json()
                    for loc in all_locs:
                        if loc["label"] == label:
                            location_map[label] = loc["id"]
                            break
                    print(f"  ⏭️  {label} (มีอยู่แล้ว)")
                    skipped += 1
                else:
                    print(f"  ❌ {label} — {res.text}")

    print(f"\n✅ ตำแหน่ง: สร้างใหม่ {created} | ข้าม {skipped}\n")
    return location_map


def create_pallets(location_map):
    print("📦 กำลังสร้างพาเลท...")
    created, skipped = 0, 0
    pallet_num = 1

    for row in ROWS:
        for slot in SLOTS:
            for level in LEVELS:
                label = f"{row}-{slot:02d}-{level}"
                loc_id = location_map.get(label)
                if not loc_id:
                    print(f"  ❌ ไม่พบ location_id สำหรับ {label}")
                    continue

                pallet_code = f"P-{pallet_num:03d}"
                res = requests.post(f"{API_URL}/pallets", json={
                    "location_id": loc_id,
                    "pallet_code": pallet_code,
                    "note": f"พาเลทประจำ {label}"
                })
                if res.status_code == 200:
                    print(f"  ✅ {pallet_code} → {label}")
                    created += 1
                elif res.status_code == 400:
                    print(f"  ⏭️  {pallet_code} (มีอยู่แล้ว)")
                    skipped += 1
                else:
                    print(f"  ❌ {pallet_code} — {res.text}")

                pallet_num += 1

    print(f"\n✅ พาเลท: สร้างใหม่ {created} | ข้าม {skipped}\n")


if __name__ == "__main__":
    print("=" * 50)
    print("🏕️  Warehouse Setup Script")
    print("=" * 50 + "\n")

    location_map = create_locations()
    create_pallets(location_map)

    print("=" * 50)
    print("🎉 Setup เสร็จแล้ว! พร้อมใช้งานได้เลยครับ")
    print("=" * 50)
