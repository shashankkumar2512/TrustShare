# Project Root

This repository contains the full-stack application:
- client/ - React frontend
- server/ - FastAPI backend

The dashboard follows the shared application structure:
- `client/src/pages/Dashboard.js` is the route-level page.
- `client/src/features/dashboard/` contains dashboard components, hooks, and services.
- `server/src/dashboard/` contains the dashboard controller, models, and database service.
- The authenticated `GET /api/dashboard/` endpoint loads all dashboard data from the application database.
# project root navigation 
cd project-root
# Start the server:
cd server
python -m src.main

# Start the client:
cd client
npm start

## PostgreSQL development environment

TrustShare uses PostgreSQL for development, integration, and production. SQLAlchemy is the application data layer and connects to PostgreSQL through `psycopg2`.

```powershell
cd project-root/server
Copy-Item .env.example .env
docker compose up --build
```

The Compose stack starts PostgreSQL 16, waits for its health check, and then starts FastAPI. Override `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` outside source control when shared credentials are required. SQLite remains available only to isolated unit tests.
