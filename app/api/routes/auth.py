from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token
from app.crud.user import authentic_user

router = APIRouter(prefix="/auth", tags=["Auth"])
db_dependency = Depends(get_db)

@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = db_dependency,
):
    user = await authentic_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(401, "Incorrect email or password")
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}