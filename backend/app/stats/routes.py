import json
import logging

from app.db import countries_collection, reports_collection
from app.redis import get_redis
from fastapi import APIRouter, Query

logger = logging.getLogger("uvicorn")

router = APIRouter(prefix="/stats", tags=["stats"])

CACHE_TTL = 300  # 5 minutes


async def _cached(key: str, builder, ttl: int = CACHE_TTL):
    """Return cached JSON if available, otherwise run *builder*, cache & return."""
    r = get_redis()
    raw = await r.get(key)
    if raw is not None:
        return json.loads(raw)
    data = await builder()
    await r.set(key, json.dumps(data, default=str), ex=ttl)
    return data


@router.get("/global")
async def global_stats():
    async def _build():
        pipeline = [
            {
                "$facet": {
                    "totals": [
                        {
                            "$group": {
                                "_id": None,
                                "total": {"$sum": 1},
                                "total_likes": {"$sum": "$likes"},
                                "total_dislikes": {"$sum": "$dislikes"},
                                "urgent_count": {
                                    "$sum": {
                                        "$cond": [{"$eq": ["$urgent", True]}, 1, 0]
                                    }
                                },
                            }
                        }
                    ],
                    "by_department": [
                        {"$group": {"_id": "$department", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                    ],
                    "by_status": [
                        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                    ],
                }
            }
        ]

        result = await reports_collection.aggregate(pipeline).to_list(1)
        facet = result[0] if result else {}

        totals = (facet.get("totals") or [{}])[0] if facet.get("totals") else {}
        dept_list = facet.get("by_department", [])
        status_list = facet.get("by_status", [])

        return {
            "total_reports": totals.get("total", 0),
            "total_likes": totals.get("total_likes", 0),
            "total_dislikes": totals.get("total_dislikes", 0),
            "urgent_count": totals.get("urgent_count", 0),
            "by_department": {d["_id"]: d["count"] for d in dept_list},
            "by_status": {d["_id"]: d["count"] for d in status_list},
        }

    return await _cached("stats:global", _build)


@router.get("/top-countries")
async def top_countries(limit: int = Query(10, ge=1, le=50)):
    """
    Top N countries by report count.
    Uses $group on the denormalized country_code field — O(R) single scan,
    no geo queries needed.
    """

    async def _build():
        pipeline = [
            {"$match": {"country_code": {"$ne": None}}},
            {"$group": {"_id": "$country_code", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ]

        results = await reports_collection.aggregate(pipeline).to_list(limit)

        # fetch countries
        codes = [r["_id"] for r in results]
        country_docs = await countries_collection.find(
            {"iso_a2": {"$in": codes}},
            {"_id": 0, "iso_a2": 1, "name": 1},
        ).to_list(None)
        name_map = {d["iso_a2"]: d["name"] for d in country_docs}

        return [
            {
                "country": name_map.get(r["_id"], r["_id"]),
                "iso_a2": r["_id"],
                "count": r["count"],
            }
            for r in results
        ]

    return await _cached(f"stats:top_countries:{limit}", _build)


@router.get("/country/{iso_a2}")
async def country_stats(iso_a2: str):
    """
    Per-country statistics using $match on country_code + $facet.
    Single indexed query, no geo operations.
    """
    code = iso_a2.upper()

    # verify the country exists and get its name
    country = await countries_collection.find_one(
        {"iso_a2": code},
        {"_id": 0, "name": 1, "iso_a2": 1},
    )
    if not country:
        return {"error": "Country not found", "country": None}

    async def _build():
        pipeline = [
            {"$match": {"country_code": code}},
            {
                "$facet": {
                    "totals": [
                        {
                            "$group": {
                                "_id": None,
                                "total": {"$sum": 1},
                                "total_likes": {"$sum": "$likes"},
                                "total_dislikes": {"$sum": "$dislikes"},
                                "urgent_count": {
                                    "$sum": {
                                        "$cond": [{"$eq": ["$urgent", True]}, 1, 0]
                                    }
                                },
                            }
                        }
                    ],
                    "by_department": [
                        {"$group": {"_id": "$department", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                    ],
                    "by_status": [
                        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                    ],
                }
            },
        ]

        result = await reports_collection.aggregate(pipeline).to_list(1)
        facet = result[0] if result else {}

        totals = (facet.get("totals") or [{}])[0] if facet.get("totals") else {}
        dept_list = facet.get("by_department", [])
        status_list = facet.get("by_status", [])

        return {
            "country": country["name"],
            "iso_a2": country["iso_a2"],
            "total_reports": totals.get("total", 0),
            "total_likes": totals.get("total_likes", 0),
            "total_dislikes": totals.get("total_dislikes", 0),
            "urgent_count": totals.get("urgent_count", 0),
            "by_department": {d["_id"]: d["count"] for d in dept_list},
            "by_status": {d["_id"]: d["count"] for d in status_list},
        }

    return await _cached(f"stats:country:{code}", _build)


@router.get("/live-feed")
async def live_feed(limit: int = Query(20, ge=1, le=50)):
    """
    Latest unresolved reports, sorted by created_at descending.
    Returns lightweight docs for a live-feed widget.
    """

    async def _build():
        cursor = (
            reports_collection.find(
                {"status": {"$ne": "RESOLVED"}},
                {
                    "_id": 1,
                    "title": 1,
                    "department": 1,
                    "location": 1,
                    "urgent": 1,
                    "status": 1,
                    "country_code": 1,
                    "created_at": 1,
                },
            )
            .sort("created_at", -1)
            .limit(limit)
        )

        results = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            results.append(doc)
        return results

    return await _cached(f"stats:live_feed:{limit}", _build, ttl=60)
