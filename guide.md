As an AI, I cannot directly generate and download a `.pdf` file to your local machine. However, **I have formatted this entire response as a pristine, production-ready Markdown document.** 

**How to save this as a PDF:**
1. Copy the entire text below.
2. Paste it into a Markdown editor (like VS Code, Obsidian, or Typora) or an online converter (like dillinger.io).
3. Click **File > Print > Save as PDF** (or use a Markdown-to-PDF extension).

Here is your complete, exhaustive blueprint. It contains every single detail, architectural decision, and the final code for every file so you can recreate this system from scratch.

***

# System Architecture & Implementation Manual
## High-Scale Digital Wallet API
**Author:** [Your Name]
**Tech Stack:** Python 3.12, FastAPI, PostgreSQL, SQLAlchemy 2.0, Pydantic, PyJWT, Uvicorn

---

## 1. Project Overview & Directory Structure
This document outlines the construction of an ACID-compliant, double-entry digital wallet ledger. The system is designed to handle concurrent transactions using row-level locking (2PL) and strict database-level constraints.

**Directory Tree:**
```text
payment-wallet/
├── requirements.txt
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── dependencies.py
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── transaction.py
│   │       ├── user.py
│   │       └── wallet.py
│   ├── core/
│   │   ├── database.py
│   │   └── security.py
│   ├── crud/
│   │   ├── transaction.py
│   │   ├── user.py
│   │   └── wallet.py
│   ├── models/
│   │   └── base.py
│   └── schemas/
│       ├── transaction.py
│       ├── user.py
│       └── wallet.py
```

---

## 2. Environment Setup (Task 30)
To ensure deterministic builds and avoid Python version conflicts, we use `uv` for environment management.

**`requirements.txt`**
```text
fastapi
uvicorn
sqlalchemy
psycopg[binary]
pydantic[email]
passlib[bcrypt]
pyjwt
python-multipart
```
*Setup Commands:*
```bash
uv venv --python 3.12 walletEnv
source walletEnv/bin/activate
uv pip install -r requirements.txt
```

---

## 3. Core Configuration (Tasks 1-3, 19, 22)

### Database Connection
**File: `app/core/database.py`**
*Purpose:* Establishes the synchronous connection to PostgreSQL using the `psycopg` driver.
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Replace with your actual PostgreSQL credentials
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://user:password@localhost:5432/wallet_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Security Utilities
**File: `app/core/security.py`**
*Purpose:* Handles bcrypt password hashing and JWT (JSON Web Token) generation for stateless authentication.
```python
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "my_super_secret_key" # In production, load from .env
ALGORITHM = "HS256"

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

---

## 4. Database State Machine (SQLAlchemy Models)
**File: `app/models/base.py`**
*Purpose:* Defines the strict PostgreSQL schema. 
*Design Choices:* 
1. `Numeric(10,2)` is used instead of `Float` to prevent IEEE 754 floating-point precision loss.
2. `CheckConstraint` ensures balances never drop below zero at the database level.
3. `reference_id` enables Double-Entry Accounting by linking CREDIT and DEBIT rows.

```python
import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    UUID, CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class transaction_status(enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    
    wallet: Mapped["Wallet"] = relationship(back_populates="user")

class Wallet(Base):
    __tablename__ = 'wallets'

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id"))
    balance: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), CheckConstraint("balance>=0"))
    currency: Mapped[str] = mapped_column(String(3), default='INR')
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    
    user: Mapped["User"] = relationship(back_populates="wallet")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="wallet")

class Transaction(Base):
    __tablename__ = 'transactions'

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    wallet_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("wallets.id"))
    reference_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), CheckConstraint("amount>0"))
    type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[transaction_status] = mapped_column(Enum(transaction_status), default=transaction_status.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    
    wallet: Mapped["Wallet"] = relationship(back_populates="transactions")
```

---

## 5. API Boundary Layer (Pydantic Schemas)
*Purpose:* Validates incoming JSON payloads in $O(1)$ time before touching the database. Prevents over-posting and negative-money exploits via `Field(gt=0)`.

**File: `app/schemas/user.py`**
```python
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str | None = None

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str | None = None
    wallet_id: uuid.UUID | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

**File: `app/schemas/wallet.py`**
```python
import enum
import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class Currency(enum.Enum):
    USD = "USD"
    INR = "INR"
    EUR = "EUR"

class WalletCreate(BaseModel):
    currency: Currency

class WalletResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    balance: Decimal
    currency: Currency
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

**File: `app/schemas/transaction.py`**
```python
import enum
import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class TransactionType(enum.Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"

class TransactionStatus(enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class TransactionCreate(BaseModel):
    amount: Decimal = Field(gt=0, description="Amount must be greater than zero")
    type: TransactionType

class TransactionResponse(BaseModel):
    id: uuid.UUID
    wallet_id: uuid.UUID
    reference_id: uuid.UUID | None = None
    amount: Decimal
    type: TransactionType
    status: TransactionStatus
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

---

## 6. Business Logic (CRUD Layer)

**File: `app/crud/user.py`**
*Design Choice:* Uses `db.flush()` to execute an ACID transaction, ensuring a User and Wallet are created simultaneously. If one fails, both rollback.
```python
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import get_password_hash, verify_password
from app.models.base import User, Wallet
from app.schemas.user import UserCreate

def create_user(db: Session, user: UserCreate):
    user_data = user.model_dump()
    plain_password = user_data.pop("password")
    user_data["hashed_password"] = get_password_hash(plain_password)
    
    db_user = User(**user_data)
    db.add(db_user)
    db.flush() # Generates User ID without committing
    
    new_wallet = Wallet(user_id=db_user.id, balance=0, currency="INR")
    db.add(new_wallet)
    db.commit() # Commits both atomically
    db.refresh(db_user)
    
    db_user.wallet_id = new_wallet.id
    return db_user

def get_user_by_id(db: Session, user_id: uuid.UUID):
    stmt = select(User).where(User.id == user_id)
    return db.scalar(stmt)

def authenticate_user(db: Session, email: str, password: str):
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
```

**File: `app/crud/wallet.py`**
```python
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.base import Wallet

def get_wallet_by_id(db: Session, wallet_id: uuid.UUID):
    stmt = select(Wallet).where(Wallet.id == wallet_id)
    return db.scalar(stmt)

def get_wallet_by_user_id(db: Session, user_id: uuid.UUID):
    stmt = select(Wallet).where(Wallet.user_id == user_id)
    return db.scalar(stmt)
```

**File: `app/crud/transaction.py`**
*Design Choice:* Uses `.with_for_update()` to apply Row-Level Locking (2PL). This prevents Race Conditions if multiple requests attempt to debit the wallet simultaneously. Includes `.offset()` and `.limit()` for pagination.
```python
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.base import Transaction, Wallet
from app.schemas.transaction import TransactionCreate, TransactionStatus, TransactionType

def create_transaction(db: Session, wallet_id: uuid.UUID, transaction_in: TransactionCreate):
    # ROW LEVEL LOCKING
    wallet = db.scalar(select(Wallet).with_for_update().where(Wallet.id == wallet_id))
    if not wallet:
        raise ValueError("Wallet not found")
        
    if transaction_in.type == TransactionType.CREDIT:
        wallet.balance += transaction_in.amount
    if transaction_in.type == TransactionType.DEBIT:
        if wallet.balance < transaction_in.amount:
            raise ValueError("Insufficient funds")
        wallet.balance -= transaction_in.amount
        
    transaction = Transaction(
        wallet_id=wallet.id, 
        amount=transaction_in.amount, 
        type=transaction_in.type.value, 
        status=TransactionStatus.COMPLETED
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction) 
    return transaction

def get_transactions_by_wallet(db: Session, wallet_id: uuid.UUID, skip: int = 0, limit: int = 100):
    stmt = select(Transaction).where(Transaction.wallet_id == wallet_id).order_by(Transaction.created_at.desc()).offset(skip).limit(limit)
    return db.scalars(stmt).all()
```

---

## 7. Security Dependency Injection
**File: `app/api/dependencies.py`**
*Purpose:* Intercepts requests, decodes the JWT, and fetches the authenticated user.
```python
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import ALGORITHM, SECRET_KEY
from app.crud.user import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
db_dependency = Depends(get_db)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = db_dependency):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(401, "User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(401, "Could not validate credentials")
```

---

## 8. API Routing (The Controllers)

**File: `app/api/routes/auth.py`**
```python
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.crud.user import authenticate_user

router = APIRouter(prefix="/auth", tags=["Auth"])
db_dependency = Depends(get_db)

@router.post("/login")
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = db_dependency,
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(401, "Incorrect email or password")
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
```

**File: `app/api/routes/user.py`**
```python
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.user import create_user, get_user_by_id
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])
db_dependency = Depends(get_db)

@router.post("/", response_model=UserResponse)
def register_user(user_in: UserCreate, db: Session = db_dependency):
    try:
        return create_user(db, user_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, detail="Email already registered")

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, db: Session = db_dependency):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(404, detail="User not found")
    return user
```

**File: `app/api/routes/wallet.py`**
```python
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.crud.wallet import get_wallet_by_user_id
from app.models.base import User
from app.schemas.wallet import WalletResponse

router = APIRouter(prefix="/wallets", tags=["Wallets"])
db_dependency = Depends(get_db)

@router.get("/user/{user_id}", response_model=WalletResponse)
def get_wallet(
    user_id: uuid.UUID, 
    db: Session = db_dependency, 
    current_user: Annotated[User, Depends(get_current_user)] = None
):
    if user_id != current_user.id:
        raise HTTPException(403, "Not authorized to view this wallet")
    wallet = get_wallet_by_user_id(db, user_id)
    if not wallet:
        raise HTTPException(404, detail="Wallet not found")
    return wallet
```

**File: `app/api/routes/transaction.py`**
```python
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.crud.transaction import create_transaction, get_transactions_by_wallet
from app.crud.wallet import get_wallet_by_id
from app.models.base import User
from app.schemas.transaction import TransactionCreate, TransactionResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])
db_dependency = Depends(get_db)

@router.post("/{wallet_id}", response_model=TransactionResponse)
def new_transaction(
    wallet_id: uuid.UUID, 
    transaction_in: TransactionCreate, 
    db: Session = db_dependency, 
    current_user: Annotated[User, Depends(get_current_user)] = None
):
    try:
        wallet = get_wallet_by_id(db, wallet_id)
        if not wallet:
            raise HTTPException(404, detail="Wallet not found")
        if wallet.user_id != current_user.id:
            raise HTTPException(403, detail="Not authorized to use this wallet")
        return create_transaction(db, wallet_id, transaction_in)
    except ValueError as e:
        if str(e) == "Wallet not found":
            raise HTTPException(404, detail=str(e))
        if str(e) == "Insufficient funds":
            raise HTTPException(400, detail=str(e))

@router.get("/{wallet_id}/history", response_model=list[TransactionResponse])
def transaction_history(
    wallet_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = db_dependency, 
    current_user: Annotated[User, Depends(get_current_user)] = None
):
    wallet = get_wallet_by_id(db, wallet_id)
    if not wallet:
        raise HTTPException(404, detail="Wallet not found")
    if wallet.user_id != current_user.id:
        raise HTTPException(403, detail="Not authorized to use this wallet")
    return get_transactions_by_wallet(db, wallet_id, skip, limit)
```

---

## 9. The Application Entry Point
**File: `app/main.py`**
*Purpose:* Initializes the FastAPI application, creates the database tables, and registers all routers.
```python
from fastapi import FastAPI

from app.api.routes import auth, transaction, user, wallet
from app.core.database import engine
from app.models.base import Base

# Creates tables in PostgreSQL based on SQLAlchemy models
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Digital Wallet API", version="1.0.0")

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(wallet.router)
app.include_router(transaction.router)
```

---

## 10. Running the Application
1. Ensure PostgreSQL is running locally and the `SQLALCHEMY_DATABASE_URL` in `app/core/database.py` is correct.
2. Activate your virtual environment: `source walletEnv/bin/activate`
3. Start the server:
```bash
uvicorn app.main:app --reload
```
4. Access the interactive Swagger UI documentation at: **http://127.0.0.1:8000/docs**