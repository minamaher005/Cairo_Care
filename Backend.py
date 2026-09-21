# backend.py
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Import the agent factory from existing Cairo Care RAG AI Agent NTI
PROJECT_NTI_DIR = os.path.join(os.path.dirname(__file__), "Cairo Care RAG AI Agent NTI")
if PROJECT_NTI_DIR not in sys.path:
    sys.path.append(PROJECT_NTI_DIR)

from agent import create_cairo_care_agent

app = FastAPI(title="Cairo Care API")

# Allow CORS so the Streamlit frontend can communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the agent once to keep it in memory and reuse the conversation checkpointer
agent = create_cairo_care_agent()

# ── In-process thread registry ────────────────────────────────────────────────
thread_registry: dict[str, dict] = {}
browser_location_store: dict[str, dict] = {}


@app.get("/")
def root():
    return {"status": "ok", "message": "Cairo Care API is running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}


# ── Chat & Location Models ───────────────────────────────────────────────────

class UserLocation(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None
    area: Optional[str] = None
    area_slug: Optional[str] = None
    display_name: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    thread_id: str
    user_location: Optional[UserLocation] = None


class ResolveLocationRequest(BaseModel):
    lat: float
    lon: float


class BrowserLocationReport(BaseModel):
    thread_id: str
    lat: float
    lon: float


# ── Location Endpoints ────────────────────────────────────────────────────────

@app.post("/api/location/resolve")
def resolve_location_endpoint(req: ResolveLocationRequest):
    """Resolve latitude & longitude into Cairo district and Vezeeta area slug."""
    from location_tools import reverse_geocode
    return reverse_geocode(req.lat, req.lon)


@app.post("/api/location/browser")
def report_browser_location(report: BrowserLocationReport):
    """Receive client-side browser GPS coordinates via direct HTTP fetch."""
    from location_tools import reverse_geocode
    res = reverse_geocode(report.lat, report.lon)
    res["source"] = "GPS دقيق"
    browser_location_store[report.thread_id] = res
    return res


@app.get("/api/location/browser/{thread_id}")
def get_browser_location(thread_id: str):
    """Return latest browser-reported location for thread."""
    return browser_location_store.get(thread_id, {})


@app.get("/api/location/ip")
def ip_location_endpoint():
    """Return user location inferred from public IP."""
    from location_tools import get_ip_location
    return get_ip_location()


# ── Chat Stream ───────────────────────────────────────────────────────────────

@app.post("/chat")
async def chat_stream(request: ChatRequest):
    # Register thread on first message (title = truncated raw user message)
    if request.thread_id not in thread_registry:
        thread_registry[request.thread_id] = {
            "thread_id": request.thread_id,
            "title": request.message[:60],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    # Inject location context for agent if provided
    prompt_content = request.message
    if request.user_location:
        loc = request.user_location
        loc_parts = []
        if loc.area:
            loc_parts.append(f"المنطقة/الحي: {loc.area}")
        if loc.area_slug:
            loc_parts.append(f"رمز فيزيتا: {loc.area_slug}")
        if loc.lat is not None and loc.lon is not None:
            loc_parts.append(f"الإحداثيات: lat={loc.lat}, lon={loc.lon}")
        if loc.display_name:
            loc_parts.append(f"العنوان: {loc.display_name}")
        if loc_parts:
            prompt_content = (
                f"[معلومات موقع المستخدم الحالي المكتشف تلقائياً: {' | '.join(loc_parts)}]\n\n"
                f"{request.message}"
            )

    def event_generator():
        try:
            # Stream tokens from LangGraph agent
            for msg, metadata in agent.stream(
                {"messages": [{"role": "user", "content": prompt_content}]},
                config={"configurable": {"thread_id": request.thread_id}},
                stream_mode="messages",
            ):
                content = getattr(msg, "content", "")
                if content and isinstance(content, str):
                    # Hide internal tool calls that return ugly raw data (like get_user_coordinates)
                    if msg.__class__.__name__ == "ToolMessage" and getattr(msg, "name", "") in ("get_user_coordinates", "reverse_geocode_location"):
                        continue
                    
                    # Wrap token in JSON to safely handle newlines/special chars in SSE
                    yield f"data: {json.dumps({'token': content})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

        yield "data: [DONE]\n\n"

    # Return as Server-Sent Events (SSE)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── Thread history endpoints ───────────────────────────────────────────────────

@app.get("/threads")
def list_threads():
    """Return all known threads sorted newest-first."""
    threads = sorted(
        thread_registry.values(),
        key=lambda t: t["created_at"],
        reverse=True,
    )
    return threads


@app.get("/threads/{thread_id}/messages")
def get_thread_messages(thread_id: str):
    """
    Reconstruct the human/assistant message history for a thread
    by reading directly from the LangGraph InMemorySaver checkpointer.
    """
    import re

    if thread_id not in thread_registry:
        raise HTTPException(status_code=404, detail="Thread not found")

    try:
        state = agent.get_state(config={"configurable": {"thread_id": thread_id}})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    messages = []
    if state and state.values:
        for msg in state.values.get("messages", []):
            role = getattr(msg, "type", None)
            content = getattr(msg, "content", "")

            if role == "human":
                clean_content = re.sub(
                    r"^\[معلومات موقع المستخدم الحالي المكتشف تلقائياً:[^\]]+\]\n\n",
                    "",
                    content,
                )
                messages.append({"role": "user", "content": clean_content})
            elif role == "ai" and content:
                messages.append({"role": "assistant", "content": content})

    return messages


@app.delete("/threads/{thread_id}")
def delete_thread(thread_id: str):
    """Remove a thread from the registry."""
    thread_registry.pop(thread_id, None)
    return {"deleted": thread_id}
