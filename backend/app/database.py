from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
import os

os.makedirs("./data", exist_ok=True)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_schema(conn)


async def _migrate_schema(conn):
    """Add columns that were introduced after the initial schema."""
    migrations = [
        ("agents", "input_guardrail_keywords", "JSON NOT NULL DEFAULT '[]'"),
        ("agents", "max_input_length",          "INTEGER NOT NULL DEFAULT 0"),
        ("agents", "response_format",           "VARCHAR(20) NOT NULL DEFAULT 'text'"),
    ]
    for table, column, definition in migrations:
        try:
            await conn.execute(
                __import__("sqlalchemy").text(
                    f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
                )
            )
        except Exception:
            pass  # Column already exists — SQLite raises OperationalError, that's fine
