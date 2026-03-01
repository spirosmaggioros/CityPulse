"""
When docker starts the backend container
should wait until mongo database is up and running
before the backend tries to connect to it.

"""

import asyncio
import json
import logging
import os
import random
import sys
from datetime import datetime, timedelta

import redis as sync_redis
from app.db import (
    check_mongo_connection,
    countries_collection,
    create_indexes,
    reports_collection,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("entrypoint")

COUNTRIES_GEOJSON_PATH = os.path.join(os.path.dirname(__file__), "countries.geojson")

# Lorem ipsum word pool
LOREM_WORDS = [
    "lorem",
    "ipsum",
    "dolor",
    "sit",
    "amet",
    "consectetur",
    "adipiscing",
    "elit",
    "sed",
    "do",
    "eiusmod",
    "tempor",
    "incididunt",
    "ut",
    "labore",
    "et",
    "dolore",
    "magna",
    "aliqua",
    "enim",
    "ad",
    "minim",
    "veniam",
    "quis",
    "nostrud",
    "exercitation",
    "ullamco",
    "laboris",
    "nisi",
    "aliquip",
    "ex",
    "ea",
    "commodo",
    "consequat",
    "duis",
    "aute",
    "irure",
    "in",
    "reprehenderit",
    "voluptate",
    "velit",
    "esse",
    "cillum",
    "fugiat",
    "nulla",
    "pariatur",
    "excepteur",
    "sint",
    "occaecat",
    "cupidatat",
    "non",
    "proident",
    "sunt",
    "culpa",
    "qui",
    "officia",
    "deserunt",
    "mollit",
    "anim",
    "id",
    "est",
    "laborum",
    "curabitur",
    "pretium",
    "tincidunt",
    "lacus",
    "nulla",
    "gravida",
    "orci",
    "odio",
    "nullam",
    "varius",
    "turpis",
    "commodo",
    "pharetra",
    "praesent",
    "dapibus",
    "neque",
    "cursus",
    "faucibus",
    "tortor",
    "egestas",
    "augue",
    "vulputate",
    "eros",
    "perspiciatis",
    "unde",
    "omnis",
    "iste",
    "natus",
    "error",
    "voluptatem",
    "accusantium",
    "doloremque",
    "laudantium",
    "nemo",
    "ipsam",
    "aspernatur",
    "odit",
    "quia",
    "consequuntur",
    "magni",
    "autem",
    "iure",
    "molestiae",
    "vero",
    "eos",
    "iusto",
    "dignissimos",
    "ducimus",
    "blanditiis",
    "praesentium",
    "deleniti",
]

TITLE_PREFIXES = [
    "Issue with",
    "Problem regarding",
    "Report about",
    "Complaint about",
    "Issue at",
    "Incident near",
    "Damage to",
    "Vandalism on",
    "Hazard at",
    "Obstruction of",
    "Malfunction of",
    "Broken",
]

TITLE_OBJECTS = [
    "streetlight",
    "pavement",
    "road sign",
    "traffic signal",
    "water pipe",
    "playground equipment",
    "park bench",
    "sidewalk",
    "intersection",
    "pedestrian crossing",
    "drainage system",
    "public facility",
    "building",
    "street corner",
    "entrance",
    "barrier",
    "manhole cover",
    "wall",
]


def generate_title() -> str:
    """Generate a unique title from word pool."""
    prefix = random.choice(TITLE_PREFIXES)
    obj = random.choice(TITLE_OBJECTS)
    location = random.choice(
        [
            "on main road",
            "near square",
            "in residential area",
            "at intersection",
            "on street",
            "near building",
        ]
    )
    return f"{prefix} {obj} {location}"


def generate_lorem_paragraph(min_sentences: int = 3, max_sentences: int = 5) -> str:
    """Generate a random Lorem Ipsum paragraph."""
    num_sentences = random.randint(min_sentences, max_sentences)
    sentences = []
    for _ in range(num_sentences):
        num_words = random.randint(8, 16)
        words = [random.choice(LOREM_WORDS) for _ in range(num_words)]
        sentence = " ".join(words).capitalize() + "."
        sentences.append(sentence)
    return " ".join(sentences)


def generate_location() -> str:
    """Generate a short lorem ipsum location (2-3 words)."""
    num_words = random.randint(3, 5)
    words = [random.choice(LOREM_WORDS) for _ in range(num_words)]
    return " ".join(words).capitalize()


def point_in_polygon(lng: float, lat: float, polygon: list) -> bool:
    """Ray casting algorithm to check if point is inside polygon."""
    x, y = lng, lat
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def point_in_multi_polygon(lng: float, lat: float, geometry: dict) -> bool:
    """Check if point is in MultiPolygon or Polygon geometry."""
    if geometry["type"] == "Polygon":
        # Polygon has coordinates as [[[lng, lat, ...]]]
        return point_in_polygon(lng, lat, geometry["coordinates"][0])
    elif geometry["type"] == "MultiPolygon":
        # MultiPolygon has coordinates as [[[[lng, lat, ...]]]]]
        for polygon in geometry["coordinates"]:
            if point_in_polygon(lng, lat, polygon[0]):
                return True
    return False


def get_bounds_from_geometry(geometry: dict) -> tuple:
    """Extract min/max lng/lat bounds from geometry."""
    coords = []
    if geometry["type"] == "Polygon":
        coords = geometry["coordinates"][0]
    elif geometry["type"] == "MultiPolygon":
        for polygon in geometry["coordinates"]:
            coords.extend(polygon[0])

    if not coords:
        return (0, 0, 0, 0)  # fallback

    lngs = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return (min(lngs), min(lats), max(lngs), max(lats))


async def sample_point_from_country(country: dict, max_tries: int = 50) -> tuple:
    """Sample a random point from within a country's geometry."""
    geometry = country.get("geometry", {})
    min_lng, min_lat, max_lng, max_lat = get_bounds_from_geometry(geometry)

    for _ in range(max_tries):
        lng = random.uniform(min_lng, max_lng)
        lat = random.uniform(min_lat, max_lat)
        if point_in_multi_polygon(lng, lat, geometry):
            return (lng, lat)

    # Fallback: return a point from the middle of bounds (usually works)
    return ((min_lng + max_lng) / 2, (min_lat + max_lat) / 2)


async def wait_for_mongo(max_retries: int = 10, delay: int = 3) -> bool:
    for attempt in range(max_retries):
        try:
            await check_mongo_connection()
            logger.info(f"[PID {os.getpid()}] MongoDB is online.")
            await create_indexes()
            return True
        except Exception as e:
            logger.warning(
                f"[PID {os.getpid()}] Attempt {attempt+1}/{max_retries}: MongoDB not ready ({e}), retrying in {delay}s..."
            )
            await asyncio.sleep(delay)
    logger.error(
        f"[PID {os.getpid()}] MongoDB is not available after several attempts. Exiting."
    )
    return False


def wait_for_redis(max_retries: int = 10, delay: int = 3) -> bool:
    host = os.getenv("REDIS_HOST", "redis")
    port = int(os.getenv("REDIS_PORT", "6379"))
    logger.info(f"[PID {os.getpid()}] Waiting for Redis at {host}:{port}...")
    for attempt in range(max_retries):
        try:
            r = sync_redis.Redis(host=host, port=port, socket_connect_timeout=5)
            r.ping()
            r.close()
            logger.info(f"[PID {os.getpid()}] Redis is online.")
            return True
        except Exception as e:
            logger.warning(
                f"[PID {os.getpid()}] Attempt {attempt+1}/{max_retries}: Redis not ready ({e}), retrying in {delay}s..."
            )
            import time

            time.sleep(delay)
    logger.error(
        f"[PID {os.getpid()}] Redis is not available after several attempts. Exiting."
    )
    return False


async def populate_countries() -> None:
    """Import countries.geojson into the countries collection if not already populated."""
    count = await countries_collection.count_documents({})
    if count > 0:
        logger.info(
            f"Countries collection already has {count} documents, skipping import."
        )
        return

    logger.info("Importing countries.geojson into MongoDB...")
    with open(COUNTRIES_GEOJSON_PATH, "r") as f:
        geojson = json.load(f)

    docs = []
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        doc = {
            "name": props.get("name"),
            "iso_a3": props.get("ISO3166-1-Alpha-3"),
            "iso_a2": props.get("ISO3166-1-Alpha-2"),
            "geometry": feature.get("geometry"),
        }
        docs.append(doc)

    if docs:
        await countries_collection.insert_many(docs)
        logger.info(f"Imported {len(docs)} countries into MongoDB.")


DEPARTMENTS = ["POLICE", "FIRE_DEPARTMENT", "MUNICIPALITY"]
STATUSES = ["OPEN", "IN_PROGRESS", "RESOLVED"]


async def populate_fake_reports(num_reports: int) -> None:
    """Insert fake report data if the reports collection is empty."""
    count = await reports_collection.count_documents({})
    if count > num_reports:
        logger.info(
            f"Reports collection already has {count} documents, skipping fake data."
        )
        return

    logger.info(f"Populating {num_reports} fake reports...")

    # Fetch all countries to sample from
    countries = await countries_collection.find({}).to_list(None)
    if not countries:
        logger.warning("No countries found in database, skipping fake reports.")
        return

    docs = []
    now = datetime.utcnow()

    for i in range(num_reports):
        # Pick a random country and sample a point from it
        country = random.choice(countries)
        lng, lat = await sample_point_from_country(country)
        created = now - timedelta(
            days=random.randint(0, 30), hours=random.randint(0, 23)
        )

        doc = {
            "title": generate_title(),
            "description": generate_lorem_paragraph(),
            "department": random.choice(DEPARTMENTS),
            "location": generate_location(),
            "coordinates": {
                "type": "Point",
                "coordinates": [round(lng, 6), round(lat, 6)],
            },
            "country_code": country.get("iso_a2") or None,
            "urgent": random.random() < 0.2,
            "status": random.choice(STATUSES),
            "likes": random.randint(0, 500),
            "dislikes": random.randint(0, 500),
            "image_url": None,
            "created_at": created.isoformat(),
        }
        docs.append(doc)

    if docs:
        await reports_collection.insert_many(docs)
        logger.info(f"Inserted {len(docs)} fake reports.")


async def populate_database(fake_reports: bool = False) -> None:
    try:
        await populate_countries()
        if fake_reports:
            await populate_fake_reports(10000)
    except Exception as e:
        logger.error(f"Error populating database: {e}")
        raise


async def main():
    if not wait_for_redis():
        return False
    success = await wait_for_mongo()
    if not success:
        return False
    await populate_database()
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
