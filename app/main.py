from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.routes import auth, transaction, user, wallet
from app.core.database import engine
from app.models.base import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Digital Wallet API", version="1.0.0", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(wallet.router)
app.include_router(transaction.router)