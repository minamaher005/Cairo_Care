import sys
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field


# =========================
# Project Path
# =========================

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))


# =========================
# Import Agent
# =========================

from agent import create_cairo_care_agent


# =========================
# FastAPI App
# =========================

app = FastAPI(
    title="Cairo Care API",
    description="Backend API for Cairo Care RAG AI Agent",
    version="1.0.0"
)


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# Create Agent
# =========================

agent = create_cairo_care_agent()


# =========================
# Location & Chat Models
# =========================

class UserLocation(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None
    area: Optional[str] = None
    area_slug: Optional[str] = None
    display_name: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    thread_id: str = Field(default="default", min_length=1)
    user_location: Optional[UserLocation] = None


class ResolveLocationRequest(BaseModel):
    lat: float
    lon: float


class BrowserLocationReport(BaseModel):
    thread_id: str
    lat: float
    lon: float


browser_location_store: dict[str, dict] = {}


# =========================
# Location Endpoints
# =========================

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


# =========================
# Home
# =========================

@app.get("/")
def home():
    return {
        "success": True,
        "message": "Cairo Care API is running"
    }


# =========================
# Health Check
# =========================

@app.get("/health")
def health():
    return {
        "success": True,
        "status": "healthy"
    }


def _prepare_prompt_with_location(request: ChatRequest) -> str:
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
    return prompt_content


# =========================
# Normal Chat
# =========================

@app.post("/chat")
def chat(request: ChatRequest):

    try:
        prompt_content = _prepare_prompt_with_location(request)
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt_content
                    }
                ]
            },
            config={
                "configurable": {
                    "thread_id": request.thread_id
                }
            }
        )

        response = result["messages"][-1].content

        return {
            "success": True,
            "response": response,
            "thread_id": request.thread_id
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "An error occurred while processing your request.",
                "error": str(e)
            }
        )


# =========================
# Streaming Chat
# =========================

@app.post("/chat/stream")
def chat_stream(request: ChatRequest):

    def generate():

        try:
            prompt_content = _prepare_prompt_with_location(request)

            for message_chunk, metadata in agent.stream(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt_content
                        }
                    ]
                },
                config={
                    "configurable": {
                        "thread_id": request.thread_id
                    }
                },
                stream_mode="messages"
            ):

                content = getattr(
                    message_chunk,
                    "content",
                    ""
                )

                if isinstance(content, str) and content:

                    data = {
                        "content": content,
                        "thread_id": request.thread_id
                    }

                    yield (
                        f"data: "
                        f"{json.dumps(data, ensure_ascii=False)}"
                        f"\n\n"
                    )

            # End of stream
            yield "data: [DONE]\n\n"

        except Exception as e:

            error_data = {
                "success": False,
                "error": str(e)
            }

            yield (
                f"data: "
                f"{json.dumps(error_data, ensure_ascii=False)}"
                f"\n\n"
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )