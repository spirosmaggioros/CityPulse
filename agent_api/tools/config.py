import json
import os
from typing import Any, Dict, List, Optional

import httpx
import redis.asyncio as aioredis
from dotenv import load_dotenv
from mistralai import Mistral
from pydantic import BaseModel, field_validator

load_dotenv()

mistral_model = "mistral-large-2512"

client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
SESSION_TTL = os.getenv("SESSION_TTL")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000")
CITYPULSE_API_KEY = os.getenv("CITYPULSE_API_KEY")

assert REDIS_HOST, "REDIS_HOST environment variable is required"
assert REDIS_PORT, "REDIS_PORT environment variable is required"
assert SESSION_TTL, "SESSION_TTL environment variable is required"
assert CITYPULSE_API_KEY, "CITYPULSE_API_KEY environment variable is required"


REDIS_PORT = int(REDIS_PORT)
SESSION_TTL = int(SESSION_TTL)

_redis = aioredis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    decode_responses=True,
    socket_connect_timeout=10,
    socket_keepalive=True,
    health_check_interval=30,
)

# shared async client
_http_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Return a module-level reusable async HTTP client."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            base_url=BACKEND_API_URL,
            timeout=30,
            limits=httpx.Limits(
                max_connections=20,
                max_keepalive_connections=10,
                keepalive_expiry=60,
            ),
        )
    return _http_client


async def close_http_client() -> None:
    global _http_client
    if _http_client is not None and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None


class LocationData(BaseModel):
    location_text: str
    longitude: float
    latitude: float

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not (-180 <= v <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        return v

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not (-90 <= v <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        return v

    def to_list(self) -> List[Any]:
        return [self.location_text, self.longitude, self.latitude]

    @classmethod
    def from_list(cls, data: List[Any]) -> "LocationData":
        if len(data) != 3:
            raise ValueError(
                "Location must be a list of [location_text, longitude, latitude]"
            )
        return cls(location_text=data[0], longitude=data[1], latitude=data[2])


class IssueDescriptionData(BaseModel):
    description: str = ""
    department: str = ""
    location: str = ""
    title: str = ""
    urgent: bool = False
    image_url: Optional[str] = None

    @field_validator("department")
    @classmethod
    def validate_department(cls, v: str) -> str:
        valid = {"", "POLICE", "FIRE_DEPARTMENT", "MUNICIPALITY"}
        if v not in valid:
            raise ValueError(
                f"Department must be one of: POLICE, FIRE_DEPARTMENT, MUNICIPALITY — got '{v}'"
            )
        return v


class WorkflowStateData(BaseModel):
    location_collected: bool = False
    issue_classified: bool = False
    awaiting_confirmation: bool = False
    image_url: Optional[str] = None


class SessionStore:
    """
    Async session store backed by Redis hashes.

    Each session is a Redis hash with key citypulse:session:<session_id>
    and three fields:
        location          → JSON: [location_text, longitude, latitude]
        issue_description → JSON: {department, title, description, location, urgent}
        workflow_state    → JSON: {location_collected, issue_classified, awaiting_confirmation, image_url}
    """

    def _key(self, session_id: str) -> str:
        return f"citypulse:session:{session_id}"

    async def get_location(self, session_id: str) -> List[Any]:
        key = self._key(session_id)
        async with _redis.pipeline() as pipe:
            pipe.hget(key, "location")
            pipe.expire(key, SESSION_TTL)
            results = await pipe.execute()

        raw = results[0]
        if raw is None:
            return []
        return json.loads(raw)

    async def set_location(self, session_id: str, location: List[Any]) -> None:
        validated = LocationData.from_list(location)
        key = self._key(session_id)
        async with _redis.pipeline() as pipe:
            pipe.hset(key, "location", json.dumps(validated.to_list()))
            pipe.expire(key, SESSION_TTL)
            await pipe.execute()

    async def get_issue(self, session_id: str) -> Dict[str, Any]:
        key = self._key(session_id)
        async with _redis.pipeline() as pipe:
            pipe.hget(key, "issue_description")
            pipe.expire(key, SESSION_TTL)
            results = await pipe.execute()

        raw = results[0]
        if raw is None:
            return IssueDescriptionData().model_dump()
        return json.loads(raw)

    async def set_issue(self, session_id: str, issue: Dict[str, Any]) -> None:
        validated = IssueDescriptionData(**issue)
        key = self._key(session_id)
        async with _redis.pipeline() as pipe:
            pipe.hset(key, "issue_description", json.dumps(validated.model_dump()))
            pipe.expire(key, SESSION_TTL)
            await pipe.execute()

    async def get_workflow_state(self, session_id: str) -> Dict[str, Any]:
        key = self._key(session_id)
        async with _redis.pipeline() as pipe:
            pipe.hget(key, "workflow_state")
            pipe.expire(key, SESSION_TTL)
            results = await pipe.execute()

        raw = results[0]
        if raw is None:
            return WorkflowStateData().model_dump()
        return json.loads(raw)

    async def set_workflow_state(self, session_id: str, state: Dict[str, Any]) -> None:
        validated = WorkflowStateData(**state)
        key = self._key(session_id)
        async with _redis.pipeline() as pipe:
            pipe.hset(key, "workflow_state", json.dumps(validated.model_dump()))
            pipe.expire(key, SESSION_TTL)
            await pipe.execute()

    async def remove(self, session_id: str) -> None:
        await _redis.delete(self._key(session_id))


session_store = SessionStore()
