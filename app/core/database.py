import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Local Docker Compose default. In every hosted environment DATABASE_URL is
# supplied by the platform (Render) and points at a managed Postgres
# (Neon / Supabase).
DEFAULT_DATABASE_URL = (
    "postgresql+psycopg_async://postgres:postgres@localhost:5432/wallet_db"
)


def _normalize_database_url(url: str) -> str:
    """Accept the plain connection string that managed providers hand out.

    Neon / Supabase / Render give a URL like ``postgresql://user:pass@host/db``
    (or the legacy ``postgres://`` scheme). SQLAlchemy needs an explicit async
    driver, so upgrade the scheme to psycopg 3's async driver while leaving an
    already-qualified URL (``postgresql+psycopg_async://``) untouched.
    """
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg_async://" + url[len("postgresql://") :]
    return url


db_url = _normalize_database_url(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))

# pool_pre_ping: free-tier Postgres (and Neon's autosuspend) drop idle
# connections; check liveness before handing a connection to a request.
engine = create_async_engine(db_url, pool_pre_ping=True)

SessionLocal = async_sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


async def get_db():
    async with SessionLocal() as session:
        yield session
