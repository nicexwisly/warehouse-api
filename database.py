import databases
import sqlalchemy
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str

    class Config:
        env_file = ".env"


settings = Settings()

database = databases.Database(settings.DATABASE_URL)
metadata = sqlalchemy.MetaData()

locations = sqlalchemy.Table(
    "locations",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("row", sqlalchemy.String(10), nullable=False),
    sqlalchemy.Column("slot", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("level", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("label", sqlalchemy.String(30), unique=True),
    sqlalchemy.Column("zone", sqlalchemy.String(20), nullable=False, server_default="tent"),
    sqlalchemy.Column("container_no", sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, server_default=sqlalchemy.func.now()),
)

pallets = sqlalchemy.Table(
    "pallets",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("location_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("locations.id"), nullable=False),
    sqlalchemy.Column("pallet_code", sqlalchemy.String(50), unique=True, nullable=False),
    sqlalchemy.Column("note", sqlalchemy.Text, nullable=True),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, server_default=sqlalchemy.func.now()),
)

items = sqlalchemy.Table(
    "items",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("pallet_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("pallets.id"), nullable=False),
    sqlalchemy.Column("item_code", sqlalchemy.String(100), nullable=False),
    sqlalchemy.Column("item_name", sqlalchemy.String(255), nullable=False),
    sqlalchemy.Column("qty", sqlalchemy.Integer, default=1),
    sqlalchemy.Column("unit", sqlalchemy.String(50), nullable=True),
    sqlalchemy.Column("note", sqlalchemy.Text, nullable=True),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, server_default=sqlalchemy.func.now()),
    sqlalchemy.Column("updated_at", sqlalchemy.DateTime, server_default=sqlalchemy.func.now(), onupdate=sqlalchemy.func.now()),
)

movement_log = sqlalchemy.Table(
    "movement_log",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("item_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("items.id"), nullable=False),
    sqlalchemy.Column("from_pallet_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("pallets.id"), nullable=True),
    sqlalchemy.Column("to_pallet_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("pallets.id"), nullable=False),
    sqlalchemy.Column("from_location_label", sqlalchemy.String(30), nullable=True),
    sqlalchemy.Column("to_location_label", sqlalchemy.String(30), nullable=False),
    sqlalchemy.Column("action", sqlalchemy.String(20), nullable=True, server_default="move"),
    sqlalchemy.Column("qty_changed", sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column("moved_by", sqlalchemy.String(100), nullable=True),
    sqlalchemy.Column("actor_user_id", sqlalchemy.String(100), nullable=True),
    sqlalchemy.Column("moved_at", sqlalchemy.DateTime, server_default=sqlalchemy.func.now()),
)


def create_tables(engine):
    metadata.create_all(engine)