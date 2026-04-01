from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# --- Location ---
class LocationCreate(BaseModel):
    row: str
    slot: int
    level: int
    zone: str = "tent"              # "tent" | "container"
    container_no: Optional[int] = None   # 1, 2, 3 สำหรับ container

class LocationOut(BaseModel):
    id: int
    row: str
    slot: int
    level: int
    label: str
    zone: Optional[str] = "tent"


# --- Pallet ---
class PalletCreate(BaseModel):
    location_id: int
    pallet_code: str
    note: Optional[str] = None

class PalletOut(BaseModel):
    id: int
    location_id: int
    pallet_code: str
    note: Optional[str]
    created_at: datetime


# --- Item ---
class ItemCreate(BaseModel):
    pallet_id: int
    item_code: str
    item_name: str
    qty: int = 1
    unit: Optional[str] = None
    note: Optional[str] = None

class ItemOut(BaseModel):
    id: int
    pallet_id: int
    item_code: str
    item_name: str
    qty: int
    unit: Optional[str]
    note: Optional[str]
    created_at: datetime

class ItemSearchResult(BaseModel):
    id: int
    item_code: str
    item_name: str
    qty: int
    unit: Optional[str]
    pallet_code: str
    location_label: str

class ItemMove(BaseModel):
    to_pallet_id: int
    moved_by: Optional[str] = None

class ItemDeduct(BaseModel):
    qty: int
    actor_name: Optional[str] = None
    actor_user_id: Optional[str] = None


# --- Movement Log ---
class MovementOut(BaseModel):
    id: int
    item_id: int
    item_name: Optional[str] = None
    item_code: Optional[str] = None
    action: Optional[str] = None
    qty_changed: Optional[int] = None
    from_location_label: Optional[str]
    to_location_label: str
    moved_by: Optional[str]
    moved_at: datetime
