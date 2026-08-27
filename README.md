# Digital Payment Wallet

A highly scalable, asynchronous digital wallet application that supports secure peer-to-peer (P2P) transfers, user authentication, and deposit management. Built with FastAPI, PostgreSQL, and a Next.js (React) frontend, this app ensures safe financial transactions using strict row-level locking strategies to prevent race conditions and deadlocks.

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
        Nginx -->|SSR / static :3000| NextJS[Next.js Frontend]
        Nginx -->|REST API /api :8000| FastAPI[FastAPI Backend]
        
        NextJS -->|REST API| FastAPI
        
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
- **Frontend:** Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS
- **Infrastructure:** Docker, Nginx

## Local Setup

### With Docker (full stack)
1. Clone the repository.
2. Run `docker compose up -d --build`.
3. Open the app at `http://localhost` (Nginx serves the frontend on `/` and the API on `/api`).
4. The API (with Swagger Docs) is at `http://localhost:8000/docs`.

### Frontend only (development)
```bash
cd frontend
cp .env.example .env.local   # optional; defaults work against a local API on :8000
npm install
npm run dev                  # http://localhost:3000
```
The dev server proxies `/api/*` to `API_PROXY_TARGET` (default `http://localhost:8000`).

## Deployment
See `deploy.sh` for AWS EC2 / Ubuntu deployment instructions.
