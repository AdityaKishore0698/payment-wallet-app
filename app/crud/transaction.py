import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Transaction, Wallet, User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionStatus,
    TransactionType,
    TransferCreate,
)


async def create_transaction(db: AsyncSession, wallet_id: uuid.UUID, transaction_in: TransactionCreate):
    wallet = await db.scalar(select(Wallet).with_for_update().where(Wallet.id == wallet_id))
    if not wallet:
        raise ValueError("Wallet not found")
    if transaction_in.type == TransactionType.CREDIT:
        wallet.balance += transaction_in.amount
    if transaction_in.type == TransactionType.DEBIT:
        if wallet.balance < transaction_in.amount:
            raise ValueError("Insufficient funds")
        wallet.balance -= transaction_in.amount
    transaction = Transaction(wallet_id=wallet.id, amount=transaction_in.amount, type=transaction_in.type.value, status="SUCCESS")
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction) 
    return transaction

async def get_transactions_by_wallet(db: AsyncSession, wallet_id: uuid.UUID, skip: int = 0, limit: int = 100):
    stmt = select(Transaction).where(Transaction.wallet_id == wallet_id).order_by(Transaction.created_at.desc()).offset(skip).limit(limit)
    result = await db.scalars(stmt)
    return result.all()

async def transfer_funds(db: AsyncSession, transfer_in: TransferCreate):
    if transfer_in.from_wallet_id == transfer_in.to_wallet_id:
        raise ValueError("Cannot transfer to the same wallet")

    wallet_ids = sorted([transfer_in.from_wallet_id, transfer_in.to_wallet_id])
    
    stmt = select(Wallet).where(Wallet.id.in_(wallet_ids)).order_by(Wallet.id).with_for_update()
    result = await db.scalars(stmt)
    wallets = result.all()
    
    if len(wallets) != 2:
        raise ValueError("One or both wallets not found")
        
    wallet_map = {w.id: w for w in wallets}
    from_wallet = wallet_map[transfer_in.from_wallet_id]
    to_wallet = wallet_map[transfer_in.to_wallet_id]
    
    if from_wallet.balance < transfer_in.amount:
        raise ValueError("Insufficient funds")
        
    from_wallet.balance -= transfer_in.amount
    to_wallet.balance += transfer_in.amount
    
    ref_id = uuid.uuid4()
    
    debit_tx = Transaction(
        wallet_id=from_wallet.id,
        amount=transfer_in.amount,
        type=TransactionType.DEBIT.value,
        reference_id=ref_id,
        status="SUCCESS"
    )
    
    credit_tx = Transaction(
        wallet_id=to_wallet.id,
        amount=transfer_in.amount,
        type=TransactionType.CREDIT.value,
        reference_id=ref_id,
        status="SUCCESS"
    )
    
    db.add(debit_tx)
    db.add(credit_tx)
    await db.commit()
    await db.refresh(debit_tx)
    await db.refresh(credit_tx)
    return debit_tx, credit_tx

async def get_contacts_by_wallet(db: AsyncSession, wallet_id: uuid.UUID):
    stmt1 = select(Transaction.reference_id).where(
        Transaction.wallet_id == wallet_id, 
        Transaction.reference_id.isnot(None)
    ).distinct()
    result = await db.scalars(stmt1)
    ref_ids = result.all()
    
    if not ref_ids:
        return []
        
    stmt2 = select(User.upi_id).join(Wallet, User.id == Wallet.user_id).join(Transaction, Wallet.id == Transaction.wallet_id).where(
        Transaction.reference_id.in_(ref_ids),
        Transaction.wallet_id != wallet_id
    ).distinct()
    
    result2 = await db.scalars(stmt2)
    return result2.all()
