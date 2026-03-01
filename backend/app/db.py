import logging
import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

logger = logging.getLogger("uvicorn")

MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = os.getenv("MONGO_PORT")
MONGO_DB = os.getenv("MONGO_DB")

assert MONGO_USER, "MONGO_USER environment variable is required"
assert MONGO_PASSWORD, "MONGO_PASSWORD environment variable is required"
assert MONGO_HOST, "MONGO_HOST environment variable is required"
assert MONGO_PORT, "MONGO_PORT environment variable is required"
assert MONGO_DB, "MONGO_DB environment variable is required"

MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin"

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]
reports_collection = db["reports"]
users_collection = db["users"]
countries_collection = db["countries"]


async def check_mongo_connection() -> None:
    try:
        await client.admin.command("ping")
        logger.info(f"[PID {os.getpid()}] Connected to MongoDB!")
    except Exception as e:
        logger.error(f"[PID {os.getpid()}] Could not connect to MongoDB: {e}")


async def create_indexes() -> None:
    try:
        await reports_collection.create_index([("coordinates", "2dsphere")])
        logger.info(f"[PID {os.getpid()}] Created 2dsphere index on coordinates")

        await reports_collection.create_index([("department", 1), ("urgent", -1)])
        logger.info(
            f"[PID {os.getpid()}] Created compound index on department and urgent"
        )

        await reports_collection.create_index("country_code")
        logger.info(f"[PID {os.getpid()}] Created index on country_code")

        await reports_collection.create_index([("status", 1), ("created_at", -1)])
        logger.info(
            f"[PID {os.getpid()}] Created compound index on status + created_at"
        )

        await users_collection.create_index("username", unique=True)
        logger.info(f"[PID {os.getpid()}] Created unique index on username")

        await countries_collection.create_index([("geometry", "2dsphere")])
        logger.info(f"[PID {os.getpid()}] Created 2dsphere index on countries.geometry")

    except Exception as e:
        logger.error(f"[PID {os.getpid()}] Error creating indexes: {e}")


async def close_mongo() -> None:
    try:
        client.close()
        logger.info(f"[PID {os.getpid()}] MongoDB client closed")
    except Exception as e:
        logger.error(f"[PID {os.getpid()}] Error closing MongoDB client: {e}")
