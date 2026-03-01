import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.auth.auth import get_current_user
from app.db import reports_collection
from app.geo_utils import find_country_code
from app.models import BatchReportItem, Department, Report, ReportStatus, ReportUpdate
from app.utils import sanitize_mongo_query, verify_api_key
from bson import ObjectId
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

router = APIRouter(prefix="/reports", tags=["reports"])


def _oid(id: str) -> ObjectId:
    # convert the string to ObjectId (mostly for queries based on the id)
    try:
        return ObjectId(id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid report id: {id}",
        )


def _doc_to_response(doc: dict) -> dict:
    # normalize for response.
    # ObjectID is not serializable
    doc["id"] = str(doc.pop("_id"))
    return doc


@router.get("")  # type: ignore
async def list_reports(
    department: Optional[str] = Query(None),
    urgent: Optional[bool] = Query(None),
    report_status: Optional[str] = Query(None, alias="status"),
    sort_by: Optional[str] = Query(None),
    sort_order: Optional[str] = Query("asc"),
) -> list[dict]:
    filters: dict[str, str | bool] = {}
    if department:
        valid_depts = [d.value for d in Department]
        if department not in valid_depts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid department. Must be one of: {', '.join(valid_depts)}",
            )
        filters["department"] = department

    if urgent is not None:
        filters["urgent"] = urgent

    if report_status:
        valid_statuses = [s.value for s in ReportStatus]
        if report_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )
        filters["status"] = report_status

    sort_order_int: int = -1 if sort_order == "desc" else 1
    sort_spec = None
    if sort_by == "urgent":
        sort_spec = [("urgent", -1)]
    elif sort_by == "likes":
        sort_spec = [("likes", sort_order_int)]

    cursor = reports_collection.find(filters)
    if sort_spec:
        cursor = cursor.sort(sort_spec)

    results = []
    async for doc in cursor:
        results.append(_doc_to_response(doc))
    return results


@router.get("/{report_id}")  # type: ignore
async def get_report(report_id: str) -> dict:
    doc = await reports_collection.find_one({"_id": _oid(report_id)})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )
    return _doc_to_response(doc)


# TEMPORARY ROUTE (THIS SHOULD BE DONE FROM THE AGENT ITSELF IN PRODUCTION)
@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_key)])  # type: ignore
async def create_report(report: Report) -> dict:
    now = datetime.now(timezone.utc)
    doc = report.model_dump(mode="json")
    doc["created_at"] = now
    doc["modified_at"] = now

    # Auto-resolve country from coordinates
    lng, lat = doc["coordinates"]["coordinates"]
    doc["country_code"] = await find_country_code(lng, lat)

    result = await reports_collection.insert_one(doc)
    return {"id": str(result.inserted_id)}


@router.post("/batch", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_key)])  # type: ignore
async def batch_create_reports(reports: list[BatchReportItem] = Body(...)) -> dict:
    """Insert many reports at once.  Protected by CITYPULSE_API_KEY.

    Every field in ``BatchReportItem`` can be set explicitly.
    ``created_at`` / ``modified_at`` default to *now* when omitted.
    ``country_code`` is auto-resolved from coordinates when omitted.
    """
    if not reports:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="reports list must not be empty",
        )

    now = datetime.now(timezone.utc)
    docs: list[dict] = []

    for item in reports:
        doc = item.model_dump(mode="json")
        doc["created_at"] = doc["created_at"] or now
        doc["modified_at"] = doc["modified_at"] or now

        # Auto-resolve country from coordinates when not supplied
        if not doc.get("country_code"):
            lng, lat = doc["coordinates"]["coordinates"]
            doc["country_code"] = await find_country_code(lng, lat)

        docs.append(doc)

    result = await reports_collection.insert_many(docs)
    return {
        "inserted": len(result.inserted_ids),
        "ids": [str(oid) for oid in result.inserted_ids],
    }


@router.put("/{report_id}")  # type: ignore
async def update_report(
    report_id: str,
    update: ReportUpdate,
    user: dict = Depends(get_current_user),
) -> dict:
    update_data = update.model_dump(exclude_none=True, mode="json")

    # Strip any fields that must never be changed via update
    for forbidden in (
        "_id",
        "id",
        "title",
        "description",
        "image_url",
        "likes",
        "dislikes",
        "created_at",
        "country_code",
    ):
        update_data.pop(forbidden, None)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    # if coordinates changed, re-resolve country_code
    if "coordinates" in update_data:
        lng, lat = update_data["coordinates"]["coordinates"]
        update_data["country_code"] = await find_country_code(lng, lat)

    update_data["modified_at"] = datetime.now(timezone.utc)
    result = await reports_collection.update_one(
        {"_id": _oid(report_id)},
        {"$set": update_data},
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    doc = await reports_collection.find_one({"_id": _oid(report_id)})
    return _doc_to_response(doc)


@router.post("/{report_id}/vote")  # type: ignore
async def vote_report(
    report_id: str,
    vote: str = Query(..., description="'upvote' or 'downvote'"),
) -> dict:
    if vote not in ("upvote", "downvote"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="vote must be 'upvote' or 'downvote'",
        )

    field = "likes" if vote == "upvote" else "dislikes"
    result = await reports_collection.update_one(
        {"_id": _oid(report_id)},
        {"$inc": {field: 1}},
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )
    doc = await reports_collection.find_one({"_id": _oid(report_id)})
    return _doc_to_response(doc)


@router.post("/{report_id}/unvote")  # type: ignore
async def unvote_report(
    report_id: str,
    vote: str = Query(..., description="'upvote' or 'downvote'"),
) -> dict:
    if vote not in ("upvote", "downvote"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="vote must be 'upvote' or 'downvote'",
        )

    field = "likes" if vote == "upvote" else "dislikes"
    # Prevent going below 0
    result = await reports_collection.update_one(
        {"_id": _oid(report_id), field: {"$gt": 0}},
        {"$inc": {field: -1}},
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or count already 0",
        )
    doc = await reports_collection.find_one({"_id": _oid(report_id)})
    return _doc_to_response(doc)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)  # type: ignore
async def delete_report(
    report_id: str,
    user: dict = Depends(get_current_user),
) -> None:
    # Fetch report first to get image_url before deleting
    doc = await reports_collection.find_one({"_id": _oid(report_id)})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    # Delete associated image file if it exists
    image_url = doc.get("image_url")
    if image_url:
        upload_dir = os.environ.get("UPLOAD_DIR", "/app/uploads")
        # image_url is like "/uploads/FILENAME.png", extract just the filename
        filename = os.path.basename(image_url)
        file_path = os.path.join(upload_dir, filename)
        try:
            os.remove(file_path)
        except OSError:
            pass  # File may already be gone

    await reports_collection.delete_one({"_id": _oid(report_id)})


# @router.post("/rag_query/", status_code=status.HTTP_200_OK, dependencies=[Depends(verify_api_key)])
# async def rag_query(
#     query: str = Query(..., description="The natural language query to search reports")
# ) -> list[dict]:
#     # For simplicity, this is a very basic implementation that does a text search on title and description.
#     # In production, you'd want to use a more sophisticated approach (e.g. embedding-based search).
#     cursor = (
#         reports_collection.find(
#             {
#                 "$text": {"$search": query},
#             },
#             {
#                 "score": {"$meta": "textScore"},
#             },
#         )
#         .sort([("score", {"$meta": "textScore"})])
#         .limit(10)
#     )

#     results = []
#     async for doc in cursor:
#         results.append(_doc_to_response(doc))
#     return results


# @router.post("/rag-query")
# async def rag_query_endpoint(db_query: str = Body(..., embed=True), dependencies=[Depends(verify_api_key)]) -> list[dict]:
#     try:
#         query_dict = json.loads(db_query)
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Invalid db_query JSON: {e}")


#     cursor = reports_collection.find(query_dict)
#     results = []
#     async for doc in cursor:
#         results.append(_doc_to_response(doc))
#     return results
@router.post("/rag-query", dependencies=[Depends(verify_api_key)])
async def rag_query_endpoint(
    # 2. Keep db_query as a Dict with embed=True
    db_query: Dict[str, Any] = Body(..., embed=True)
) -> list[dict]:

    try:
        print(f"Incoming query: {db_query}")
        safe_query = sanitize_mongo_query(db_query)
        print(f"Safe query: {safe_query}")
    except ValueError as e:
        print(f"Validation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Server Error: {e}")
        raise HTTPException(status_code=400, detail="Invalid query payload format.")

    cursor = reports_collection.find(safe_query).limit(2000)
    results = []
    async for doc in cursor:
        results.append(_doc_to_response(doc))

    return results


@router.get("/closest/", status_code=status.HTTP_200_OK)  # type: ignore
async def closest_reports(
    lng: float = Query(...),
    lat: float = Query(...),
    radius_meters: float = Query(1000, description="Search radius in meters", le=20000),
    limit: int = Query(10, description="Max nearby reports"),
    department: Optional[str] = Query(None),
    urgent: Optional[bool] = Query(None),
    report_status: Optional[str] = Query(None, alias="status"),
) -> list[dict]:

    if not (-180 <= lng <= 180):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Longitude must be between -180 and 180",
        )
    if not (-90 <= lat <= 90):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Latitude must be between -90 and 90",
        )

    match_filters: dict = {}
    if department:
        valid_depts = [d.value for d in Department]
        if department not in valid_depts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid department. Must be one of: {', '.join(valid_depts)}",
            )
        match_filters["department"] = department
    if urgent is not None:
        match_filters["urgent"] = urgent
    if report_status:
        if report_status == "unresolved":
            match_filters["status"] = {"$in": ["OPEN", "IN_PROGRESS"]}
        else:
            valid_statuses = [s.value for s in ReportStatus]
            if report_status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
                )
            match_filters["status"] = report_status

    pipeline: list[dict] = [
        {
            "$geoNear": {
                "near": {
                    "type": "Point",
                    "coordinates": [lng, lat],
                },
                "distanceField": "distance",
                "maxDistance": radius_meters,
                "spherical": True,
            }
        },
    ]
    if match_filters:
        pipeline.append({"$match": match_filters})
    pipeline.append({"$limit": limit})

    cursor = reports_collection.aggregate(pipeline)

    results = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        results.append(doc)

    return results
