import logging

from app.db import countries_collection
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger("uvicorn")

router = APIRouter(prefix="/geo", tags=["geo"])


@router.get("/country")
async def get_country(
    lng: float = Query(..., description="Longitude"),
    lat: float = Query(..., description="Latitude"),
):
    """
    Given a lat/lng, return the country that contains the point.
    Returns the country name, ISO codes, and the full polygon geometry
    so the client can cache it for efficient client-side point-in-polygon checks.
    """
    point = {"type": "Point", "coordinates": [lng, lat]}

    country = await countries_collection.find_one(
        {"geometry": {"$geoIntersects": {"$geometry": point}}},
        {"_id": 0, "name": 1, "iso_a3": 1, "iso_a2": 1, "geometry": 1},
    )

    if not country:
        return {"country": None}

    return {
        "country": {
            "name": country["name"],
            "iso_a3": country.get("iso_a3", ""),
            "iso_a2": country.get("iso_a2", ""),
            "geometry": country["geometry"],
        }
    }
