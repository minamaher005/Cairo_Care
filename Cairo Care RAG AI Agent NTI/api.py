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
# Request Model
# =========================

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    thread_id: str = Field(default="default", min_length=1)


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


# =========================
# Normal Chat
# =========================

@app.post("/chat")
def chat(request: ChatRequest):

    try:

        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": request.message
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

            for message_chunk, metadata in agent.stream(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": request.message
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