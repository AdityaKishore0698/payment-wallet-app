import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.crud.transaction import create_transaction, get_transactions_by_wallet, transfer_funds, get_contacts_by_wallet
from app.crud.wallet import get_wallet_by_id
from app.models.base import User
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransferCreate

router = APIRouter(prefix="/transactions", tags=["Transactions"])

db_dependency = Depends(get_db)
current_user_dependency = Depends(get_current_user)

@router.post("/transfer", response_model=list[TransactionResponse])
async def transfer_money(transfer_in: TransferCreate, db: AsyncSession = db_dependency, current_user: User = current_user_dependency):
    try:
        from_wallet = await get_wallet_by_id(db, transfer_in.from_wallet_id)
        if not from_wallet:
            raise HTTPException(404, detail="Sender wallet not found")
        if from_wallet.user_id != current_user.id:
            raise HTTPException(403, detail="Not authorized to use this wallet")
            
        debit_tx, credit_tx = await transfer_funds(db, transfer_in)
        return [debit_tx, credit_tx]
    except ValueError as e:
        raise HTTPException(400, detail=str(e))

@router.post("/{wallet_id}", response_model=TransactionResponse)
async def new_transaction(wallet_id: uuid.UUID, transaction_in: TransactionCreate, db: AsyncSession = db_dependency, current_user: User = current_user_dependency):
    try:
        wallet = await get_wallet_by_id(db, wallet_id)
        if not wallet:
            raise HTTPException(404)
        if wallet.user_id!=current_user.id:
            raise HTTPException(403, "Not authorized to use this wallet")
        return await create_transaction(db, wallet_id, transaction_in)
    except ValueError as e:
        if str(e) == "Wallet not found":
            raise HTTPException(404, detail=str(e))
        if str(e) == "Insufficient funds":
            raise HTTPException(400, detail=str(e))

@router.get("/{wallet_id}/history", response_model=list[TransactionResponse])
async def transaction_history(wallet_id: uuid.UUID, skip: int = 0, limit: int = 100, db: AsyncSession = db_dependency, current_user: User = current_user_dependency):
    wallet = await get_wallet_by_id(db, wallet_id)
    if not wallet:
        raise HTTPException(404)
    if wallet.user_id!=current_user.id:
        raise HTTPException(403, detail="Not authorized to use this wallet")
    return await get_transactions_by_wallet(db, wallet_id, skip, limit)

@router.get("/{wallet_id}/contacts", response_model=list[str])
async def transaction_contacts(wallet_id: uuid.UUID, db: AsyncSession = db_dependency, current_user: User = current_user_dependency):
    wallet = await get_wallet_by_id(db, wallet_id)
    if not wallet:
        raise HTTPException(404)
    if wallet.user_id!=current_user.id:
        raise HTTPException(403, detail="Not authorized to use this wallet")
    return await get_contacts_by_wallet(db, wallet_id)