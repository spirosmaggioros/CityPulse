"""
Geo utility: look up the ISO Alpha-2 country code for a given coordinate.
Uses MongoDB $geoIntersects with the 2dsphere-indexed countries collection.
"""

from typing import Optional

from app.db import countries_collection


async def find_country_code(lng: float, lat: float) -> Optional[str]:
    """
    Query the countries collection to find which country contains
    the given [lng, lat] point.
    """
    doc = await countries_collection.find_one(
        {
            "geometry": {
                "$geoIntersects": {
                    "$geometry": {"type": "Point", "coordinates": [lng, lat]}
                }
            }
        },
        {"_id": 0, "iso_a2": 1},
    )
    if doc:
        return doc.get("iso_a2") or None
    return None
