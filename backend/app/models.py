from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from app.utils import clean_string
from pydantic import BaseModel, Field, field_validator, model_validator


class Department(str, Enum):
    POLICE = "POLICE"
    FIRE_DEPARTMENT = "FIRE_DEPARTMENT"
    MUNICIPALITY = "MUNICIPALITY"


class ReportStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


class UserCreate(BaseModel):
    username: str
    password: str

    @field_validator("username", mode="before")  # type: ignore
    @classmethod
    def clean_username(cls, v: str) -> str:
        return clean_string(v, titlecase=False)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: str
    username: str


class CoordinatesGeoJSON(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]

    @field_validator("coordinates")  # type: ignore
    @classmethod
    def validate_coordinates(cls, v: List[float]) -> List[float]:
        if len(v) != 2:
            raise ValueError(
                "Coordinates must have exactly 2 values [longitude, latitude]"
            )
        if not (-180 <= v[0] <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        if not (-90 <= v[1] <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        return v


class Report(BaseModel):
    department: Department
    location: str
    coordinates: CoordinatesGeoJSON
    title: str
    description: str
    urgent: bool
    image_url: Optional[str] = None
    country_code: Optional[str] = None  # ISO 3166-1 Alpha-2 (2 chars, set by backend)
    likes: int = 1
    dislikes: int = 0
    status: ReportStatus = ReportStatus.OPEN
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    modified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("title", mode="before")  # type: ignore
    @classmethod
    def clean_title(cls, v: str) -> str:
        return clean_string(v, titlecase=True)

    @field_validator("location", "description", mode="before")  # type: ignore
    @classmethod
    def clean_text_fields(cls, v: str) -> str:
        return clean_string(v, titlecase=False)

    @field_validator("image_url", mode="before")  # type: ignore
    @classmethod
    def clean_image_url(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return clean_string(v, titlecase=False)
        return v

    @field_validator("coordinates")  # type: ignore
    @classmethod
    def validate_coordinates(cls, v: CoordinatesGeoJSON) -> CoordinatesGeoJSON:
        if not isinstance(v, CoordinatesGeoJSON):
            raise ValueError(
                "Coordinates must be a CoordinatesGeoJSON object with type 'Point' and coordinates [longitude, latitude]"
            )
        return v

    @field_validator("likes", "dislikes")  # type: ignore
    @classmethod
    def validate_counts(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Likes and dislikes cannot be negative")
        return v

    @field_validator("image_url")  # type: ignore
    @classmethod
    def validate_image_url_for_fire_department(
        cls, v: Optional[str], info: dict
    ) -> Optional[str]:
        department = info.data.get("department") if hasattr(info, "data") else None
        if department == Department.FIRE_DEPARTMENT and not v:
            raise ValueError("image_url is required for FIRE_DEPARTMENT reports")
        return v

    @model_validator(mode="after")
    def validate_fire_department_image_url(self):
        if self.department == Department.FIRE_DEPARTMENT and not self.image_url:
            raise ValueError("image_url is required for FIRE_DEPARTMENT reports")
        return self


class ReportUpdate(BaseModel):
    department: Optional[Department] = None
    location: Optional[str] = None
    coordinates: Optional[CoordinatesGeoJSON] = None
    urgent: Optional[bool] = None
    status: Optional[ReportStatus] = None

    @field_validator("location", mode="before")  # type: ignore
    @classmethod
    def clean_text_fields_update(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return clean_string(v, titlecase=False)
        return v

    @field_validator("coordinates")  # type: ignore
    @classmethod
    def validate_coordinates_update(
        cls, v: Optional[CoordinatesGeoJSON]
    ) -> Optional[CoordinatesGeoJSON]:
        if v is not None:
            if not isinstance(v, CoordinatesGeoJSON):
                raise ValueError(
                    "Coordinates must be a CoordinatesGeoJSON object with type 'Point' and coordinates [longitude, latitude]"
                )
        return v


class BatchReportItem(BaseModel):
    """Schema for a single report in a batch-insert payload.

    All fields are required except ``image_url``, ``country_code``,
    ``created_at`` and ``modified_at`` which have sensible defaults.
    The fire-department image_url rule is **not** enforced here
    because this endpoint is used for administrative data seeding.
    """

    department: Department
    location: str
    coordinates: CoordinatesGeoJSON
    title: str
    description: str
    urgent: bool
    image_url: Optional[str] = None
    country_code: Optional[str] = None
    likes: int = 1
    dislikes: int = 0
    status: ReportStatus = ReportStatus.OPEN
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, v: str) -> str:
        return clean_string(v, titlecase=True)

    @field_validator("location", "description", mode="before")
    @classmethod
    def clean_text(cls, v: str) -> str:
        return clean_string(v, titlecase=False)

    @field_validator("image_url", mode="before")
    @classmethod
    def clean_image(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return clean_string(v, titlecase=False)
        return v
