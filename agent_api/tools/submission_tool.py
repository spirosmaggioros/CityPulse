import json
import os
from typing import Any, Optional

from pydantic import BaseModel, Field

from .config import (
    CITYPULSE_API_KEY,
    client,
    get_http_client,
    mistral_model,
    session_store,
)

SUBMISSION_TOOL = {
    "type": "function",
    "function": {
        "name": "submit_issue",
        "description": """
            Given similar issues from the same neighborhood,
            search for the same exact issue. If no similar issue 
            is found nearby, then it will submit the issue to our database.
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


async def submit_issue(user_query: str, session_id: str = "") -> Any:
    location = await session_store.get_location(session_id)
    issue_description = await session_store.get_issue(session_id)

    class SimilaritySearchAgent(BaseModel):
        similar_issue_found: bool = Field(
            description="True if a similar issue is found, False otherwise"
        )
        similar_issue: Optional[str] = Field(
            description="Return the id of the similar issue(if found)"
        )

    http = get_http_client()
    response = await http.get(
        "/reports/closest/",
        params={
            "lng": location[1],
            "lat": location[2],
            "radius_meters": 2000,
        },
    )

    chat_response = client.chat.parse(
        model=mistral_model,
        messages=[
            {
                "role": "system",
                "content": """
                    You are a duplicate issue detector for a city reporting platform.

                    Your task is to compare a newly reported issue against a list of nearby existing issues
                    and determine whether any of them describe the SAME real-world problem.

                    Rules:
                    - Consider issues duplicates if they refer to the same physical problem at the same location,
                    even if described differently (e.g. "broken streetlight" vs "light not working on main street").
                    - Do NOT flag as duplicate if the issues are merely similar in category but at different locations
                    or are clearly distinct problems.
                    - If a duplicate is found, return: match_found=True and the id of the matching issue.
                    The system will automatically upvote the existing issue on the user's behalf.
                    - If no duplicate is found, return: match_found=False and id=None.
                    The system will proceed to submit the new issue to the database.
                    - Be strict: when in doubt, return match_found=False.
                """,
            },
            {
                "role": "user",
                "content": f"""
                    New report: {user_query}

                    Nearby existing issues:
                    {response.json()}

                    Is any of the existing issues the same problem as the new report?
                """,
            },
        ],
        response_format=SimilaritySearchAgent,
        temperature=0.1,
    )

    similar_issue_search = json.loads(chat_response.choices[0].message.content)

    if not similar_issue_search["similar_issue_found"]:
        payload = {
            "department": issue_description["department"],
            "coordinates": {
                "type": "Point",
                "coordinates": [location[1], location[2]],
            },
            "location": location[0],
            "title": issue_description["title"],
            "description": issue_description["description"],
            "urgent": issue_description["urgent"],
        }
        if issue_description.get("image_url"):
            payload["image_url"] = issue_description["image_url"]
        response = await http.post(
            "/reports", json=payload, headers={"Authorization": CITYPULSE_API_KEY}
        )
    else:
        # assert similar_issue_search["similar_issue"] is not None
        response = await http.post(
            f"/reports/{similar_issue_search['similar_issue']}/vote?vote=upvote"
        )

        # report not submitted — delete the uploaded image
        if issue_description.get("image_url"):
            disk_path = issue_description["image_url"].lstrip("/")
            try:
                os.remove(disk_path)
            except OSError:
                pass

    await session_store.remove(session_id)
    return similar_issue_search
