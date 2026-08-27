import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, transaction, user, wallet
from app.core.database import engine
from app.models.base import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Digital Wallet API", version="1.0.0", lifespan=lifespan)

# The hosted frontend (Vercel) and API (Render) live on different origins, so
# CORS must allow the deployed frontend. FRONTEND_URL is the canonical
# production origin; local dev origins are always allowed. Vercel preview
# deployments get unique URLs — allow them via the *.vercel.app regex unless
# FRONTEND_URL_REGEX overrides it.
_allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
_frontend_url = os.getenv("FRONTEND_URL")
if _frontend_url:
    _allowed_origins.append(_frontend_url.rstrip("/"))

_origin_regex = os.getenv("FRONTEND_URL_REGEX", r"https://.*\.vercel\.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(wallet.router)
app.include_router(transaction.router)