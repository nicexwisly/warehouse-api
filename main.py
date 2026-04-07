import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import database, metadata, settings
from routers import locations, pallets, items, history, master
import sqlalchemy

app = FastAPI(
    title="Warehouse API",
    description="ระบบจัดการสินค้าในเต้นท์และตู้คอนเทนเนอร์",
    version="1.0.0",
)

cors_origins_env = os.getenv("CORS_ORIGINS", "")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(locations.router)
app.include_router(pallets.router)
app.include_router(items.router)
app.include_router(history.router)
app.include_router(master.router)


def run_migrations(engine):
    migrations = [
        "ALTER TABLE movement_log ADD COLUMN IF NOT EXISTS action VARCHAR(20) DEFAULT 'move'",
        "ALTER TABLE movement_log ADD COLUMN IF NOT EXISTS qty_changed INTEGER",
        "ALTER TABLE movement_log ADD COLUMN IF NOT EXISTS actor_user_id VARCHAR(100)",
        "ALTER TABLE locations ADD COLUMN IF NOT EXISTS zone VARCHAR(20) DEFAULT 'tent'",
        "ALTER TABLE locations ADD COLUMN IF NOT EXISTS container_no INTEGER",
        "ALTER TABLE locations ALTER COLUMN label TYPE VARCHAR(30)",
        "ALTER TABLE movement_log ALTER COLUMN from_location_label TYPE VARCHAR(30)",
        "ALTER TABLE movement_log ALTER COLUMN to_location_label TYPE VARCHAR(30)",
        "ALTER TABLE locations ALTER COLUMN row TYPE VARCHAR(10)",
        "UPDATE locations SET zone = 'container' WHERE row LIKE 'CON%' AND (zone IS NULL OR zone = 'tent')",
        "UPDATE locations SET zone = 'tent' WHERE row NOT LIKE 'CON%' AND zone IS NULL",
        # make timestamp columns timezone-aware going forward
        "ALTER TABLE locations ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'",
        "ALTER TABLE pallets ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'",
        "ALTER TABLE items ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'",
        "ALTER TABLE items ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'",
        "ALTER TABLE movement_log ALTER COLUMN moved_at TYPE TIMESTAMPTZ USING moved_at AT TIME ZONE 'UTC'",
        "ALTER TABLE locations ALTER COLUMN created_at SET DEFAULT TIMEZONE('utc', CURRENT_TIMESTAMP)",
        "ALTER TABLE pallets ALTER COLUMN created_at SET DEFAULT TIMEZONE('utc', CURRENT_TIMESTAMP)",
        "ALTER TABLE items ALTER COLUMN created_at SET DEFAULT TIMEZONE('utc', CURRENT_TIMESTAMP)",
        "ALTER TABLE items ALTER COLUMN updated_at SET DEFAULT TIMEZONE('utc', CURRENT_TIMESTAMP)",
        "ALTER TABLE movement_log ALTER COLUMN moved_at SET DEFAULT TIMEZONE('utc', CURRENT_TIMESTAMP)",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(sqlalchemy.text(sql))
            except Exception:
                pass
        conn.commit()


@app.on_event("startup")
async def startup():
    await database.connect()
    engine = sqlalchemy.create_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
    )
    metadata.create_all(engine)
    run_migrations(engine)
    master.load_master()
    engine.dispose()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/")
async def root():
    return {"message": "Warehouse API is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
