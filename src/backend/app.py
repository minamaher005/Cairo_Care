"""FastAPI Application for Cairo Care."""
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

try:
    from src.backend.agent import create_cairo_care_agent
    from src.backend.tools.location_tools import reverse_geocode, get_ip_location
except ImportError:
    from agent import create_cairo_care_agent
    from tools.location_tools import reverse_geocode, get_ip_location

app = FastAPI(
    title="Cairo Care API",
    description="Intelligent medical routing, emergency dispatch, and doctor discovery for Greater Cairo.",
    version="1.0.0",
)

# CORS middleware for Streamlit and external web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the LangGraph agent in memory
agent = create_cairo_care_agent()

# In-process registries for sessions & browser-reported GPS
thread_registry: dict[str, dict] = {}
browser_location_store: dict[str, dict] = {}


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Cairo Care API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


# ── Pydantic Request & Response Schemas ────────────────────────────────────────

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


# ── Geolocation Endpoints ─────────────────────────────────────────────────────

@app.post("/api/location/resolve")
def resolve_location_endpoint(req: ResolveLocationRequest):
    """Resolve latitude & longitude into Cairo district and Vezeeta area slug."""
    return reverse_geocode(req.lat, req.lon)


@app.post("/api/location/browser")
def report_browser_location(report: BrowserLocationReport):
    """Receive client-side browser GPS coordinates via direct HTTP fetch."""
    res = reverse_geocode(report.lat, report.lon)
    res["source"] = "GPS دقيق"
    browser_location_store[report.thread_id] = res
    return res


@app.get("/api/location/browser/{thread_id}")
def get_browser_location(thread_id: str):
    """Return latest browser-reported location for a conversation thread."""
    return browser_location_store.get(thread_id, {})


@app.get("/api/location/ip")
def ip_location_endpoint():
    """Return user location inferred from public IP."""
    return get_ip_location()


# ── Chat Streaming (SSE) ──────────────────────────────────────────────────────

def _prepare_prompt_with_location(message: str, user_location: Optional[UserLocation]) -> str:
    if not user_location:
        return message

    loc_parts = []
    if user_location.area:
        loc_parts.append(f"المنطقة/الحي: {user_location.area}")
    if user_location.area_slug:
        loc_parts.append(f"رمز فيزيتا: {user_location.area_slug}")
    if user_location.lat is not None and user_location.lon is not None:
        loc_parts.append(f"الإحداثيات: lat={user_location.lat}, lon={user_location.lon}")
    if user_location.display_name:
        loc_parts.append(f"العنوان: {user_location.display_name}")

    if loc_parts:
        return (
            f"[معلومات موقع المستخدم الحالي المكتشف تلقائياً: {' | '.join(loc_parts)}]\n\n"
            f"{message}"
        )
    return message


@app.post("/chat")
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream token-by-token responses from the Cairo Care agent via Server-Sent Events.
    Supports both /chat and /chat/stream.
    """
    if request.thread_id not in thread_registry:
        thread_registry[request.thread_id] = {
            "thread_id": request.thread_id,
            "title": request.message[:60],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    prompt_content = _prepare_prompt_with_location(request.message, request.user_location)

    def event_generator():
        try:
            for message_chunk, metadata in agent.stream(
                {"messages": [{"role": "user", "content": prompt_content}]},
                config={"configurable": {"thread_id": request.thread_id}},
                stream_mode="messages",
            ):
                chunk = message_chunk.content
                if chunk and isinstance(chunk, str):
                    payload = {"token": chunk, "content": chunk}
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

            yield "data: [DONE]\n\n"
        except Exception as e:
            err = {"error": str(e), "token": f"⚠️ خطأ: {e}", "content": f"⚠️ خطأ: {e}"}
            yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Thread & History Endpoints ────────────────────────────────────────────────

@app.get("/threads")
def list_threads():
    """Return all conversation threads ordered newest first."""
    threads = list(thread_registry.values())
    threads.sort(key=lambda t: t.get("created_at", ""), reverse=True)
    return threads


@app.get("/threads/{thread_id}/messages")
def get_thread_messages(thread_id: str):
    """
    Reconstruct message history for a thread from the LangGraph InMemorySaver checkpointer.
    """
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
    """Remove a thread from the session registry."""
    thread_registry.pop(thread_id, None)
    return {"deleted": thread_id}
