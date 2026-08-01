# Digital Payment Wallet

A highly scalable, asynchronous digital wallet application that supports secure peer-to-peer (P2P) transfers, user authentication, and deposit management. Built with FastAPI, PostgreSQL, and Streamlit, this app ensures safe financial transactions using strict row-level locking strategies to prevent race conditions and deadlocks.

## Screenshots

<!-- Add your screenshots to a folder named "assets" in the repository, then replace these placeholder images! -->

| Login & Registration | Interactive Dashboard |
|:---:|:---:|
| <img src="assets/login.png" width="400"/> | <img src="assets/dashboard.png" width="400"/> |

| P2P Transfer & Add Funds | Transaction History |
|:---:|:---:|
| <img src="assets/transfer.png" width="400"/> | <img src="assets/history.png" width="400"/> |

## System Architecture

Our application is built as a highly robust, multi-container architecture orchestrated by Docker Compose:

```mermaid
graph TD
    Client([User Browser]) -->|HTTP :80| Nginx[Nginx Reverse Proxy]
    
    subgraph Internal Docker Network
        Nginx -->|WebSockets :8501| Streamlit[Streamlit Frontend]
        Nginx -->|REST API :8000| FastAPI[FastAPI Backend]
        
        Streamlit -->|REST API| FastAPI
        
        FastAPI -->|asyncpg| DB[(PostgreSQL)]
        FastAPI -->|Message Queue| Redis[(Redis Broker)]
        Redis --> Celery[Celery Background Worker]
        Celery -->|Email / Heavy Tasks| External([External Services])
    end
```

### Safe Financial Concurrency
To safely handle hundreds of simultaneous money transfers without double-spending, the database enforces ACID compliance using strict row-level locking during transfers.

```mermaid
sequenceDiagram
    participant Sender
    participant API as FastAPI
    participant DB as PostgreSQL
    participant Receiver

    Sender->>API: POST /transfer (UPI, Amount)
    API->>DB: Fetch Wallets with SELECT FOR UPDATE (Lock)
    DB-->>API: Wallet Data
    API->>API: Verify Balance
    API->>DB: Debit Sender, Credit Receiver
    API->>DB: Create Transaction Records
    API->>DB: COMMIT Transaction (Unlock)
    API-->>Sender: Transfer Successful
```

## Features
- **User Authentication:** Secure JWT-based login and registration (Bcrypt password hashing).
- **UPI-Style Discovery:** Discover receivers safely using a `username@wallet` style ID without exposing personal data.
- **Deadlock-Free P2P Transfers:** Guaranteed safe concurrent transactions via deterministic database locking.
- **Cursor Pagination:** High-performance Keyset pagination for infinite-scroll transaction histories.
- **Service-Oriented Architecture:** Includes Redis caching and Celery for asynchronous background task processing.
- **Containerized:** Fully Dockerized with Docker Compose for seamless deployment behind an Nginx Load Balancer.

## Tech Stack
- **Backend:** FastAPI, Python 3.12, SQLAlchemy 2.0, asyncpg, Celery
- **Database / Cache:** PostgreSQL 15, Redis
- **Frontend:** Streamlit, Pandas
- **Infrastructure:** Docker, Nginx

## Local Setup
1. Clone the repository.
2. Run `docker compose up -d --build`.
3. The frontend is accessible at `http://localhost:8501`.
4. The API (with Swagger Docs) is at `http://localhost:8000/docs`.

## Deployment
See `deploy.sh` for AWS EC2 / Ubuntu deployment instructions.
