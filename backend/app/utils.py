import html

import pyvips
from fastapi import FastAPI, Header, HTTPException, Depends
import os
from typing import Any, Dict, List  

SAFE_OPERATORS = {
    "$eq", "$gt", "$gte", "$lt", "$lte",
    "$in", "$nin",
    "$and", "$or", "$not", "$nor",
    "$exists", "$type",
    "$all", "$elemMatch", "$size",
    "$regex", "$options", 
    "$near", "$geometry", "$maxDistance", "$geoWithin", "$box", "$polygon", "$centerSphere"
}
ALLOWED_FIELDS = {
    "department", "location", "coordinates", "title", "description",
    "urgent", "image_url", "country_code", "likes", "dislikes",
    "status", "created_at", "modified_at"
}
def sanitize_mongo_query(query: Any) -> Any:
    if isinstance(query, list):
        return [sanitize_mongo_query(item) for item in query]
    
    if isinstance(query, dict):
        clean_query = {}
        for key, value in query.items():

            if key.startswith("$"):
                if key not in SAFE_OPERATORS:
                    raise ValueError(f"Dangerous or unsupported operator detected: {key}")
            else:

                base_field = key.split(".")[0]
                if base_field not in ALLOWED_FIELDS:
                    raise ValueError(f"Querying on unauthorized field: {base_field}")
            
            if isinstance(value, (dict, list)):
                clean_query[key] = sanitize_mongo_query(value)
            else:
                clean_query[key] = value
                
        return clean_query
    
    return query

# only internal apis use this
CITYPULSE_API_KEY = os.getenv("CITYPULSE_API_KEY")
async def verify_api_key(authorization: str = Header(None)):
    if authorization != CITYPULSE_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
def clean_string(value: str, titlecase: bool = False) -> str:
    value = value.strip()
    value = html.unescape(value)
    if titlecase:
        value = value.title()
    return value


def compress_image(
    image_data: bytes,
    max_size: int = 768,
    quality: int = 75,
) -> bytes:

    if max_size <= 0:
        raise ValueError("max_size must be > 0")
    if not 1 <= quality <= 100:
        raise ValueError("quality must be between 1 and 100")

    img = pyvips.Image.new_from_buffer(image_data, "", access="sequential")

    if getattr(img, "n_pages", 1) > 1:
        img = img[0]

    if img.hasalpha():
        img = img.flatten(background=[255, 255, 255])

    longest = max(img.width, img.height)
    if longest > max_size:
        scale = max_size / longest
        img = img.resize(scale, kernel=pyvips.enums.Kernel.LANCZOS3)

    return img.write_to_buffer(".webp", Q=quality)
