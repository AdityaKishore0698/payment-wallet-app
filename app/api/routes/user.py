import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.user import create_user, get_user_by_id
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])

db_dependency = Depends(get_db)

@router.post("/", response_model=UserResponse)
async def register_user(user_in: UserCreate, db: AsyncSession = db_dependency):
    try:
        return await create_user(db, user_in)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, detail="Email already registered")

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: uuid.UUID, db: AsyncSession = db_dependency):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(404, detail="User not found")
    return user
