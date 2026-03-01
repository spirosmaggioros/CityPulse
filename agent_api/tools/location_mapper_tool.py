import json
import os
from typing import Any, Tuple

from pydantic import BaseModel, Field

from .config import client, get_http_client, mistral_model, session_store

LOCATION_MAPPER_TOOL = {
    "type": "function",
    "function": {
        "name": "location_mapper",
        "description": "Translates user's given address to [longitude, latitude]",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                },
            },
            "required": [
                "user_query",
            ],
        },
    },
}


async def get_coordinates(location: str) -> Tuple[float, float]:
    url = "https://api.mapbox.com/search/geocode/v6/forward"

    params = {
        "q": location,
        "access_token": os.getenv("MAPBOX_API_KEY"),
        "limit": 1,
    }

    http = get_http_client()
    response = await http.get(url, params=params)
    response.raise_for_status()

    data = response.json()

    if not data.get("features"):
        raise ValueError(f"No coordinates found for location: {location}")

    coordinates = data["features"][0]["geometry"]["coordinates"]
    longitude, latitude = coordinates

    return longitude, latitude


async def location_mapper(user_query: str, session_id: str = "") -> Any:
    class LocationMapperAgent(BaseModel):
        location: str = Field(description="Extracted location of user's query")
        longitude: float = Field(description="Longitude of given address")
        latitude: float = Field(description="Latitude of given address")

    chat_response = client.chat.parse(
        model=mistral_model,
        messages=[
            {
                "role": "system",
                "content": """
                    Understand user's given query and only extract the location/address of the text.
                """,
            },
            {
                "role": "user",
                "content": f"""
                    This is user's query regarding the location: {user_query}
                """,
            },
        ],
        response_format=LocationMapperAgent,
        temperature=0,
    )

    location_details = json.loads(chat_response.choices[0].message.content)

    location_text = location_details["location"]
    longitude, latitude = await get_coordinates(location_text)

    await session_store.set_location(
        session_id,
        [
            location_details["location"],
            longitude,
            latitude,
        ],
    )

    return location_details
