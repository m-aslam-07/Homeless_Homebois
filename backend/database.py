from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://logitech:logitech123@postgres:5432/logitech_db"
)

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_db():
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Initialize database tables.
    For hackathon: Drop and recreate tables to handle schema changes.
    In production, use Alembic migrations instead.
    """
    try:
        async with engine.begin() as conn:
            # Drop all tables (for hackathon - allows schema changes)
            await conn.run_sync(Base.metadata.drop_all)
            # Create all tables with new schema
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Database tables initialized successfully")
    except Exception as e:
        print(f"⚠️ Database initialization error: {e}")
        # Try to create tables anyway (in case drop fails)
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                print("✅ Database tables created (drop failed, but create succeeded)")
        except Exception as e2:
            print(f"❌ Critical: Could not initialize database: {e2}")
            raise
