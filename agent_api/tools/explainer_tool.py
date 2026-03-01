import json
from typing import Any

from pydantic import BaseModel, Field

from .config import CITYPULSE_API_KEY, client, get_http_client, mistral_model

EXPLAINER_TOOL = {
    "type": "function",
    "function": {
        "name": "problem_classifier",
        "description": """
            Given a user query about a specific region statistics, yield a valid query for our database
            so that needed pins are extracted and explain the results.
        """,
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


async def fetch_pins_from_db(db_query: str) -> list[dict]:
    try:
        if isinstance(db_query, str):
            db_query = json.loads(db_query)
        http = get_http_client()
        response = await http.post(
            "/reports/rag-query",
            json={"db_query": db_query},
            headers={"Authorization": CITYPULSE_API_KEY},
        )
        response.raise_for_status()
    except Exception:
        return []

    data = response.json()

    # if len(data) > 2000:
    # data = data[:2000]

    return data


async def explainer(user_query: str) -> Any:

    class ExplainerAgent(BaseModel):
        db_query: str = Field(
            description=(
                "A valid MongoDB filter as a JSON string, e.g. "
                '{"department": "FIRE_DEPARTMENT", "status": "OPEN", "country_code": "CY"}. '
                "Use only fields from the Report model. Return ONLY the JSON object, no explanation."
            )
        )

    step1_response = client.chat.parse(
        model=mistral_model,
        messages=[
            {
                "role": "system",
                "content": """
                    You are a data query assistant.
                    Given a natural-language question about regional statistics,
                    produce the minimal database query required to fetch the relevant pins/reports.
                    Return only a db_query field — no explanation.

                    Here is our Report base model:
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
                """,
            },
            {"role": "user", "content": user_query},
        ],
        response_format=ExplainerAgent,
    )

    parsed = step1_response.choices[0].message.parsed

    db_query = parsed.db_query
    pins = await fetch_pins_from_db(str(db_query))

    pins = str(pins)

    step2_response = client.chat.complete(
        model=mistral_model,
        messages=[
            {
                "role": "system",
                "content": """
                    You are a regional statistics analyst.
                    You will be given a user question and a list of data pins/reports
                    fetched from the database. Use only those pins to answer the question
                    accurately and concisely.
                    
                    Important Context:
                        More Upvotes(or likes) indicate that this issue is critical, as many people want this issue to be closed. 
                        More Downvotes(or dislikes) indicate that this issue is probably false.
                """,
            },
            {
                "role": "user",
                "content": (
                    f"User question: {user_query}\n\n" f"Retrieved pins:\n{pins}"
                ),
            },
        ],
    )

    explanation = step2_response.choices[0].message.content

    return explanation
