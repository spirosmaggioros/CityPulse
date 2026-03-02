import os
import uuid
from typing import Annotated, Literal, Optional

import chainlit as cl
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_mistralai import ChatMistralAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from tools.config import mistral_model, session_store
from tools.explainer_tool import explainer
from tools.location_mapper_tool import location_mapper
from tools.problem_classifier_tool import problem_classifier
from tools.submission_tool import submit_issue
from typing_extensions import TypedDict

load_dotenv()


class CityPulseState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str
    location_collected: bool
    issue_classified: bool
    awaiting_confirmation: bool
    image_url: Optional[str]
    explanation: Optional[str]
    reset: bool


llm = ChatMistralAI(model=mistral_model, temperature=0.2)


def _delete_upload(image_url: str | None) -> None:
    """Remove an uploaded image file from disk (best-effort)."""
    if not image_url:
        return
    disk_path = image_url.lstrip("/")
    try:
        os.remove(disk_path)
    except OSError:
        pass


async def explainer_node(state: CityPulseState) -> dict:
    last_human = next(
        (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        "",
    )

    result = await explainer(user_query=last_human)

    return {
        "messages": [AIMessage(content=result)],
        "explanation": result,
    }


async def reset_node(state: CityPulseState) -> dict:
    session_id = state.get("session_id", "")
    _delete_upload(state.get("image_url"))
    await session_store.remove(session_id)
    return {
        "messages": [],
        "session_id": session_id,
        "location_collected": False,
        "issue_classified": False,
        "awaiting_confirmation": False,
        "image_url": None,
        "reset": True,
    }


def ask_for_location_node(state: CityPulseState) -> dict:
    return {
        "messages": [
            AIMessage(
                content="Got it! Could you also share the **location or address** where this issue is occurring?"
            )
        ]
    }


def ask_for_issue_node(state: CityPulseState) -> dict:
    return {
        "messages": [
            AIMessage(
                content="Got it! Now could you describe the **issue** you're experiencing at that location?"
            )
        ]
    }


def supervisor_node(state: CityPulseState) -> dict:
    location_collected = state.get("location_collected", False)
    issue_classified = state.get("issue_classified", False)
    awaiting_confirmation = state.get("awaiting_confirmation", False)

    last_human = next(
        (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        "",
    )

    if location_collected and issue_classified:
        reset_response = llm.invoke(
            [
                HumanMessage(
                    content=f"""Does this message indicate the user wants to start a new/fresh issue report, separate from any previous one?
            User message: "{last_human}"

            Reply with only YES or NO."""
                )
            ]
        )

        if reset_response.content.strip().upper() == "YES":
            return {"messages": [AIMessage(content="__route:reset__")]}

    explain_keywords = [
        "highest",
        "lowest",
        "most",
        "crime rate",
        "statistics",
        "how many",
        "which city",
        "compare",
        "show me data",
        "worst",
        "best",
    ]

    if any(kw in last_human.lower() for kw in explain_keywords):
        return {"messages": [AIMessage(content="__route:explainer__")]}

    if awaiting_confirmation:
        confirm_keywords = [
            "yes",
            "submit",
            "submit it",
            "confirm",
            "looks good",
            "correct",
            "ok",
            "sure",
        ]
        if any(kw in last_human.lower() for kw in confirm_keywords):
            return {"messages": [AIMessage(content="__route:submission__")]}
        else:
            return {"messages": [AIMessage(content="__route:end__")]}

    detection_response = llm.invoke(
        [
            HumanMessage(
                content=f"""Analyze this user message and determine what they are providing.
        User message: "{last_human}"

        Reply with ONLY one of these labels:
        - LOCATION — if the message is primarily giving a location, address, or place name
        - ISSUE — if the message is primarily describing a problem, incident, or issue (even without a location)
        - BOTH — if the message contains both a location and an issue description
        - UNCLEAR — if it's neither"""
            )
        ]
    )

    detected = detection_response.content.strip().upper()

    if detected == "BOTH":
        if not location_collected:
            return {"messages": [AIMessage(content="__route:location_mapper__")]}
        elif not issue_classified:
            return {"messages": [AIMessage(content="__route:problem_classifier__")]}
        else:
            return {"messages": [AIMessage(content="__route:submission__")]}

    elif detected == "LOCATION":
        if not location_collected:
            return {"messages": [AIMessage(content="__route:location_mapper__")]}
        elif not issue_classified:
            return {"messages": [AIMessage(content="__route:ask_for_issue__")]}

    elif detected == "ISSUE":
        if not issue_classified:
            return {"messages": [AIMessage(content="__route:problem_classifier__")]}
        elif not location_collected:
            return {"messages": [AIMessage(content="__route:ask_for_location__")]}

    if not location_collected:
        return {"messages": [AIMessage(content="__route:ask_for_location__")]}
    if not issue_classified:
        return {"messages": [AIMessage(content="__route:ask_for_issue__")]}

    return {"messages": [AIMessage(content="__route:submission__")]}


async def location_mapper_node(state: CityPulseState) -> dict:
    last_human = next(
        (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        "",
    )
    session_id = state.get("session_id", "")

    result = await location_mapper(user_query=last_human, session_id=session_id)
    location_name = result["location"]

    return {
        "messages": [
            AIMessage(
                content=f"Got it — I've located **{location_name}**. Could you describe the issue you're experiencing there?"
            )
        ],
        "location_collected": True,
    }


async def problem_classifier_node(state: CityPulseState) -> dict:
    last_human = next(
        (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        "",
    )
    image_url = state.get("image_url")
    session_id = state.get("session_id", "")

    result = await problem_classifier(
        user_query=last_human, image_url=image_url, session_id=session_id
    )

    if result.get("error"):
        return {
            "messages": [AIMessage(content=result["message"])],
            "issue_classified": False,
            "awaiting_confirmation": False,
        }

    department = result.get("department", "MUNICIPALITY")
    title = result.get("title", "Issue")
    description = result.get("description", last_human)
    urgent = result.get("urgent", False)
    urgent_label = " 🚨 **(Urgent)**" if urgent else ""

    summary = (
        f"I've classified this as **{department}**{urgent_label}: *{title}*\n\n"
        f"{description}\n\n"
        f"If this looks right to you, say **'submit it'** to report it."
    )

    return {
        "messages": [AIMessage(content=summary)],
        "issue_classified": True,
        "awaiting_confirmation": True,
        "image_url": None,
    }


async def submission_node(state: CityPulseState) -> dict:
    last_human = next(
        (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        "",
    )

    if not state.get("location_collected") or not state.get("issue_classified"):
        return {
            "messages": [
                AIMessage(
                    content="I'm missing some information. Could you share the location and issue description again?"
                )
            ],
            "awaiting_confirmation": False,
        }

    result = await submit_issue(
        user_query=last_human, session_id=state.get("session_id", "")
    )

    if result.get("similar_issue_found"):
        msg = "A similar issue has already been reported nearby. Your report was not submitted to avoid duplicates."
    else:
        msg = "✅ Your issue has been successfully submitted to CityPulse!"

    return {
        "messages": [AIMessage(content=msg)],
        "awaiting_confirmation": False,
    }


def end_node(state: CityPulseState) -> dict:
    return {
        "messages": [
            AIMessage(
                content="No problem! Let me know if you'd like to report something else."
            )
        ]
    }


def route_from_supervisor(
    state: CityPulseState,
) -> Literal[
    "location_mapper",
    "problem_classifier",
    "submission",
    "end",
    "reset",
    "explainer",
    "ask_for_location",
    "ask_for_issue",
]:
    last_ai = next(
        (m.content for m in reversed(state["messages"]) if isinstance(m, AIMessage)),
        "",
    )
    if "__route:location_mapper__" in last_ai:
        return "location_mapper"
    elif "__route:problem_classifier__" in last_ai:
        return "problem_classifier"
    elif "__route:submission__" in last_ai:
        return "submission"
    elif "__route:reset__" in last_ai:
        return "reset"
    elif "__route:explainer__" in last_ai:
        return "explainer"
    elif "__route:ask_for_location__" in last_ai:
        return "ask_for_location"
    elif "__route:ask_for_issue__" in last_ai:
        return "ask_for_issue"
    else:
        return "end"


builder = StateGraph(CityPulseState)

builder.add_node("ask_for_location", ask_for_location_node)
builder.add_node("ask_for_issue", ask_for_issue_node)
builder.add_node("supervisor", supervisor_node)
builder.add_node("location_mapper", location_mapper_node)
builder.add_node("problem_classifier", problem_classifier_node)
builder.add_node("submission", submission_node)
builder.add_node("end", end_node)
builder.add_node("reset", reset_node)
builder.add_node("explainer", explainer_node)

builder.add_edge(START, "supervisor")
builder.add_conditional_edges(
    "supervisor",
    route_from_supervisor,
    {
        "location_mapper": "location_mapper",
        "problem_classifier": "problem_classifier",
        "submission": "submission",
        "explainer": "explainer",
        "end": "end",
        "reset": "reset",
        "ask_for_location": "ask_for_location",
        "ask_for_issue": "ask_for_issue",
    },
)
builder.add_edge("location_mapper", END)
builder.add_edge("problem_classifier", END)
builder.add_edge("submission", END)
builder.add_edge("explainer", END)
builder.add_edge("end", END)
builder.add_edge("reset", END)
builder.add_edge("ask_for_location", END)
builder.add_edge("ask_for_issue", END)


graph = builder.compile()


@cl.on_chat_start
async def on_chat_start() -> None:
    session_id = cl.context.session.id
    cl.user_session.set(
        "graph_state",
        {
            "messages": [],
            "session_id": session_id,
            "location_collected": False,
            "issue_classified": False,
            "awaiting_confirmation": False,
            "image_path": None,
            "reset": False,
        },
    )
    await session_store.set_workflow_state(
        session_id,
        {
            "location_collected": False,
            "issue_classified": False,
            "awaiting_confirmation": False,
            "image_url": None,
        },
    )

    actions = [
        cl.Action(
            name="go_home",
            label="🏠 Back to Home",
            payload={},
        ),
        cl.Action(
            name="starter_most_urgent_issue",
            label="🛑 Explore most urgent issues",
            payload={
                "message": "Show me the most urgent issue in Greece. Explain your thought process."
            },
        ),
        cl.Action(
            name="starter_most_upvoted_issue",
            label="🔍 Compare country statistics",
            payload={
                "message": "Compare Greece's crime rate with Argentina's crime rate. Explain the results."
            },
        ),
        cl.Action(
            name="starter_explain_crime_rate",
            label="📊 Explore city statistics",
            payload={
                "message": "Which city has the highest crime rate in Greece? Explain the results"
            },
        ),
    ]

    await cl.Message(
        content=(
            "👋 Welcome to **CityPulse**! Here's what I can help you with:\n\n"
            "🚧 **Report a city issue** — First give me your location, then describe an issue at this specific location (e.g. potholes, broken lights, flooding) and I'll classify and submit it to the right department.\n\n"
            "📊 **Explore city statistics** — Ask about crime rates, issue counts, or compare data across districts.\n\n"
            "🚨 **Flag urgent hazards** — Reports marked as urgent get escalated automatically.\n\n"
            "👇 **Tap a suggestion below to get started, or just give me your location to start an issue!**"
        ),
        actions=actions,
    ).send()


@cl.action_callback("go_home")
async def on_go_home(action: cl.Action) -> None:
    """Navigate to home page. Client-side JavaScript will handle the navigation."""
    await cl.Message(
        content="🏠 Redirecting to home...\n\nIf not redirected, [click here](/)."
    ).send()
    # Note: The actual navigation is handled by the frontend
    # Chainlit will trigger a page redirect via response headers


@cl.action_callback("starter_explain_crime_rate")
@cl.action_callback("starter_most_urgent_issue")
@cl.action_callback("starter_most_upvoted_issue")
async def on_starter_action(action: cl.Action) -> None:
    message_text = action.payload.get("message", "")
    await on_message(cl.Message(content=message_text))


@cl.on_chat_end
async def on_chat_end() -> None:
    state: CityPulseState | None = cl.user_session.get("graph_state")
    if state:
        _delete_upload(state.get("image_url"))
    await session_store.remove(cl.context.session.id)


@cl.on_message
async def on_message(message: cl.Message) -> None:
    state: CityPulseState = cl.user_session.get("graph_state")
    session_id = state.get("session_id", cl.context.session.id)

    # Restore workflow flags from Redis (source of truth)
    workflow = await session_store.get_workflow_state(session_id)
    state["location_collected"] = workflow["location_collected"]
    state["issue_classified"] = workflow["issue_classified"]
    state["awaiting_confirmation"] = workflow["awaiting_confirmation"]
    state["image_url"] = workflow.get("image_url")

    for element in message.elements:
        if isinstance(element, cl.Image) and element.path:
            import pyvips

            os.makedirs("uploads", exist_ok=True)
            filename = f"{uuid.uuid4()}.webp"
            save_path = f"uploads/{filename}"
            image = pyvips.Image.new_from_file(element.path, access="sequential")
            image.webpsave(save_path, Q=80, strip=True)
            state["image_url"] = f"/uploads/{filename}"
            print(f"Image stored: {save_path} -> /uploads/{filename}")
            break

    state["messages"].append(HumanMessage(content=message.content))

    try:
        result = await graph.ainvoke(state)

        if result.get("reset"):
            result["messages"] = []
            cl.user_session.set("graph_state", result)
            # Reset workflow state in Redis
            await session_store.set_workflow_state(
                session_id,
                {
                    "location_collected": False,
                    "issue_classified": False,
                    "awaiting_confirmation": False,
                    "image_url": None,
                },
            )
            await cl.Message(
                content="🔄 Starting fresh! Please share the **address or location** of the new issue."
            ).send()
            return
    except Exception as e:
        await cl.Message(content=f"🔴 Internal error: {e}").send()
        return

    cl.user_session.set("graph_state", result)

    # Persist workflow flags to Redis
    await session_store.set_workflow_state(
        session_id,
        {
            "location_collected": result.get("location_collected", False),
            "issue_classified": result.get("issue_classified", False),
            "awaiting_confirmation": result.get("awaiting_confirmation", False),
            "image_url": result.get("image_url"),
        },
    )

    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and not msg.content.startswith("__route:"):
            await cl.Message(content=msg.content).send()
            break


if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    run_chainlit(__file__)
