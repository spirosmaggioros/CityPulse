import logging
import os
from contextlib import asynccontextmanager

from app import db
from app.auth.routes import router as auth_router
from app.geo.routes import router as geo_router
from app.redis import check_redis_connection, close_redis
from app.reports.routes import router as reports_router
from app.stats.routes import router as stats_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

logger = logging.getLogger("uvicorn")


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    # Startup
    await check_redis_connection()
    logger.info("✓ Redis connection verified")

    await db.check_mongo_connection()
    await db.create_indexes()
    logger.info("✓ MongoDB connection verified")

    yield

    # Shutdown
    await db.close_mongo()
    await close_redis()


app: FastAPI = FastAPI(lifespan=lifespan)

# app.add_middleware(
# CORSMiddleware,
# allow_origins=["*"],
# allow_credentials=True,
# allow_methods=["*"],
# allow_headers=["*"],
# )

app.include_router(auth_router)
app.include_router(reports_router)
app.include_router(geo_router)
app.include_router(stats_router)


@app.get("/ping")  # type: ignore
async def ping() -> HTMLResponse:
    return HTMLResponse(content="<p>ping</p>", status_code=200)
