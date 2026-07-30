import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Transaction, Wallet
from app.schemas.transaction import (
    TransactionCreate,
    TransactionStatus,
    TransactionType,
)


def create_transaction(db: Session, wallet_id: uuid.UUID, transaction_in: TransactionCreate):
    wallet = db.scalar(select(Wallet).with_for_update().where(Wallet.id == wallet_id))
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
    db.commit()
    db.refresh(transaction) 
    return transaction

def get_transactions_by_wallet(db: Session, wallet_id: uuid.UUID, skip: int = 0, limit: int = 100):
    stmt = select(Transaction).where(Transaction.wallet_id == wallet_id).order_by(Transaction.created_at.desc()).offset(skip).limit(limit)
    return db.scalars(stmt).all()
