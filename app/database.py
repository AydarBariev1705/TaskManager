from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, 
    bind=engine, class_=AsyncSession,
    )


Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
