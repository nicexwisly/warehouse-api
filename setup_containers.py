"""
Setup Script: เพิ่มตำแหน่งและพาเลทตู้คอนเทนเนอร์
--------------------------------------------------
รัน: python setup_containers.py

จะสร้าง:
- 24 ตำแหน่ง (3 ตู้ x 2 แถว x 4 ล็อค)  CON1-A-1 ถึง CON3-B-4
- 24 พาเลท (PC-001 ถึง PC-024)
"""

import requests

API_URL = "https://warehouse-api-njvm.onrender.com"  # ← แก้ให้ตรงกับ URL ของคุณ

CONTAINERS = [1, 2, 3]
ROWS = ["A", "B"]
SLOTS = [1, 2, 3, 4]


def get_all_locations():
    return requests.get(f"{API_URL}/locations").json()


def create_container_locations():
    print("📍 กำลังสร้างตำแหน่งตู้คอนเทนเนอร์...")
    created, skipped = 0, 0
    location_map = {}   # "CON1-A-1" → location_id

    for con in CONTAINERS:
        for row in ROWS:
            for slot in SLOTS:
                key = f"CON{con}-{row}-{slot}"
                row_val = f"CON{con}{row}"   # เก็บใน DB เช่น "CON1A"
                res = requests.post(f"{API_URL}/locations", json={
                    "row": row_val,
                    "slot": slot,
                    "level": 1,
                })
                if res.status_code == 200:
                    location_map[key] = res.json()["id"]
                    print(f"  ✅ {key}")
                    created += 1
                elif res.status_code == 400:
                    # มีอยู่แล้ว — หา id จาก list
                    for loc in get_all_locations():
                        if loc["row"] == row_val and loc["slot"] == slot and loc["level"] == 1:
                            location_map[key] = loc["id"]
                            break
                    print(f"  ⏭️  {key} (มีอยู่แล้ว)")
                    skipped += 1
                else:
                    print(f"  ❌ {key} — {res.text}")

    print(f"\n✅ ตำแหน่ง: สร้างใหม่ {created} | ข้าม {skipped}\n")
    return location_map


def create_container_pallets(location_map):
    print("📦 กำลังสร้างพาเลทตู้คอนเทนเนอร์...")
    created, skipped = 0, 0
    pallet_num = 1

    for con in CONTAINERS:
        for row in ROWS:
            for slot in SLOTS:
                key = f"CON{con}-{row}-{slot}"
                loc_id = location_map.get(key)
                if not loc_id:
                    print(f"  ❌ ไม่พบ location_id สำหรับ {key}")
                    pallet_num += 1
                    continue

                pallet_code = f"PC-{pallet_num:03d}"
                res = requests.post(f"{API_URL}/pallets", json={
                    "location_id": loc_id,
                    "pallet_code": pallet_code,
                    "note": f"พาเลทประจำ {key}",
                })
                if res.status_code == 200:
                    print(f"  ✅ {pallet_code} → {key}")
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
    print("🚛  Container Setup Script")
    print("=" * 50 + "\n")
    location_map = create_container_locations()
    create_container_pallets(location_map)
    print("=" * 50)
    print("🎉 Setup เสร็จแล้ว! พร้อมใช้งานได้เลยครับ")
    print("=" * 50)
