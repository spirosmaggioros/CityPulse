import base64
import json
from typing import Any, Optional

from pydantic import BaseModel, Field

from .config import client, mistral_model, session_store

PROBLEM_CLASSIFIER_TOOL = {
    "type": "function",
    "function": {
        "name": "problem_classifier",
        "description": """
            Given a short description of the issue and optionally an image,
            classify the problem into 1 of 3 categories and provide a title
            for the given issue.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                },
                "image_url": {
                    "type": "string",
                    "description": "Must be a valid base64 encoded image string starting with 'data:image/'. Do NOT invent or guess URLs. Only provide this if the user has explicitly uploaded an image in this conversation. If unsure, omit this field entirely.",
                },
            },
            "required": [
                "user_query",
            ],
        },
    },
}


async def problem_classifier(
    user_query: str, image_url: Optional[str] = None, session_id: str = ""
) -> Any:

    class ProblemClassifierAgent(BaseModel):
        department: str = Field(
            description="Either POLICE, FIRE_DEPARTMENT or MUNICIPALITY"
        )
        title: str = Field(description="Short title for the given issue")
        description: str = Field(description="User's given description of the issue")
        urgent: bool = Field(description="Specify if the issue is urgent or not")
        image_url: Optional[str] = Field(
            description="(Optional) An image of the given issue"
        )
        verified: bool = Field(
            description="True if the image clearly confirms the reported issue, False otherwise"
        )

    user_content = [
        {
            "type": "text",
            "text": user_query,
        }
    ]

    if image_url:
        # image_url is stored as "/uploads/FILE" for the browser;
        # on disk the file lives at "uploads/FILE" (relative to /app workdir)
        disk_path = image_url.lstrip("/")
        with open(disk_path, "rb") as f:
            data = f.read()
        image_data = f"data:image/webp;base64,{base64.b64encode(data).decode('utf-8')}"

        user_content.append(
            {
                "type": "image_url",
                "image_url": {"url": image_data},
            }
        )

    chat_response = client.chat.parse(
        model=mistral_model,
        messages=[
            {
            "role": "system",
            "content": """
                You are a city issue classifier for a civic reporting platform. Your job is to evaluate
                and classify issues reported by citizens.

                ## Step 1: Relevance & Importance Check
                First, determine if the issue is worth submitting. REJECT the issue (set department to 
                "REJECTED") if it falls into any of these categories:

                - **Trivial or personal complaints** (e.g. "my neighbor is loud", "I don't like the 
                new park benches", "a dog barked at me")
                - **Non-civic matters** (e.g. private property disputes, personal grievances, 
                complaints about other citizens' behavior that don't affect public safety)
                - **Vague or nonsensical reports** (e.g. "something is wrong", "I don't know", 
                gibberish, test messages)
                - **Issues outside city jurisdiction** (e.g. federal matters, private business 
                complaints, national infrastructure)
                - **Spam or offensive content**

                ACCEPT the issue if it relates to:
                - Public safety hazards (fires, crimes, dangerous structures)
                - Infrastructure problems (potholes, broken streetlights, damaged signs)
                - Environmental issues (illegal dumping, flooding, fallen trees blocking roads)
                - Public property damage or vandalism
                - Any situation requiring emergency services

                ## Step 2: Classification (only if ACCEPTED)
                Classify the issue into exactly one of: POLICE, FIRE_DEPARTMENT, MUNICIPALITY

                ## Step 3: Fill in the fields
                - **Title** — write a short, specific title (e.g. "Large pothole on Main St.")
                - **Description** — extract and clean the user's description
                - **Urgency** — set True ONLY if there is immediate risk to life or property
                - **Verified** — whether the image (if provided) confirms the reported issue

                ## FIRE_DEPARTMENT Rules (strictly enforced)
                - Only classify as FIRE_DEPARTMENT if an image is provided AND it clearly shows 
                visible flames, heavy smoke, burning material, or an active fire hazard.
                - If no image is provided for a fire report → set verified=False.
                - If the image does NOT clearly show fire → set verified=False.
                - If the image is blurry, unclear, or irrelevant → do not classify as FIRE_DEPARTMENT.

                ## Image Verification
                - If an image is provided, factor what you see into your classification decision.
                - Classify based on what the image actually shows, not just what the user claims.
                - Reject mismatched reports (e.g. image shows a pothole but user says "fire").
            """,
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
        response_format=ProblemClassifierAgent,
        temperature=0.2,
    )

    issue_details = json.loads(chat_response.choices[0].message.content)

    if issue_details["department"] == "REJECTED":
        return {
            "error": True,
            "message": "Your report doesn't appear to be a civic issue we can action on. Please describe a public safety or infrastructure problem.",
        }
    if issue_details["department"] == "FIRE_DEPARTMENT" and not image_url:
        return {
            "error": True,
            "message": "🔥 Fire department issues require an image to verify. Please upload a photo of the situation.",
        }
    if (
        issue_details["department"] == "FIRE_DEPARTMENT"
        and not issue_details["verified"]
    ):
        return {
            "error": True,
            "message": "🔥 The image you provided does not clearly show a fire. Please upload a clearer photo to proceed.",
        }

    location = await session_store.get_location(session_id)

    await session_store.set_issue(
        session_id,
        {
            "department": issue_details["department"],
            "title": issue_details["title"],
            "description": issue_details["description"],
            "location": location[0] if location else "",
            "urgent": issue_details["urgent"],
            "image_url": image_url if image_url else None,
        },
    )

    return issue_details
