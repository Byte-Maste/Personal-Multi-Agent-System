from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db, engine, Base
from app.routers import auth, upload, transactions, dashboard, insights, alerts, goals, scenarios, family, agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from app.services.seed_service import seed_default_categories
    async for db in get_db():
        await seed_default_categories(db)
        break
    yield


app = FastAPI(title="Personal Finance Agent API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(insights.router, prefix="/insights", tags=["Insights"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
app.include_router(goals.router, prefix="/goals", tags=["Goals"])
app.include_router(scenarios.router, prefix="/scenarios", tags=["Scenarios"])
app.include_router(family.router, prefix="/family", tags=["Family"])
app.include_router(agent.router, prefix="/agent", tags=["Agent"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
