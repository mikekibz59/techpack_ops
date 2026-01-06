from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = (
    "sqlite+aiosqlite:///./data/app.db"  # TODO: MAKE SURE WE ARE GOING TO LOAD THIS FROM .ENV FILES AT RUNTIME.
)

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_async_session():
    async with async_session() as session:
        yield session
