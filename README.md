# Digital Payment Wallet

A highly scalable, asynchronous digital wallet application that supports secure peer-to-peer (P2P) transfers, user authentication, and deposit management. Built with FastAPI, PostgreSQL, and Streamlit, this app ensures safe financial transactions using strict row-level locking strategies to prevent race conditions and deadlocks.

## Features
- **User Authentication:** Secure JWT-based login and registration (Bcrypt password hashing).
- **UPI-Style Discovery:** Discover receivers safely using a `username@wallet` style ID without exposing personal data.
- **Deadlock-Free P2P Transfers:** Guaranteed safe concurrent transactions via deterministic database locking.
- **Cursor Pagination:** High-performance Keyset pagination for infinite-scroll transaction histories.
- **Service-Oriented Architecture:** Includes Redis caching and Celery for asynchronous background task processing.
- **Containerized:** Fully Dockerized with Docker Compose for seamless deployment behind an Nginx Load Balancer.

## Tech Stack
- **Backend:** FastAPI, Python 3.11, SQLAlchemy 2.0, asyncpg, Celery
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
