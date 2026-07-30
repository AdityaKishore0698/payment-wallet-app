from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

db_url = "postgresql+psycopg_async://postgres:postgres@localhost:5432/wallet_db"

engine = create_async_engine(db_url)

SessionLocal = async_sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

async def get_db():
    async with SessionLocal() as session:
        yield session