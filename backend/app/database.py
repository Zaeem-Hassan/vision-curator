"""Database engine, session factory, and base model."""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# ── Async engine (used by the FastAPI HTTP layer) ─────────────────────────────
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ── Sync engine (used by the background ML pipeline thread) ───────────────────
# Derive the sync URL from the async one (strip the +aiosqlite / +asyncpg prefix)
_sync_url = settings.DATABASE_URL.replace(
    "sqlite+aiosqlite", "sqlite"
).replace(
    "postgresql+asyncpg", "postgresql+psycopg2"
)
sync_engine = create_engine(
    _sync_url,
    connect_args={"check_same_thread": False} if _sync_url.startswith("sqlite") else {},
    pool_pre_ping=True,
)
SyncSession = sessionmaker(bind=sync_engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """Dependency that yields an async database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables (async, called at startup)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def init_db_sync() -> None:
    """Create all tables (sync, callable from threads)."""
    Base.metadata.create_all(sync_engine)
