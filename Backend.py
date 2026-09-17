# backend.py
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Import the agent factory from your existing agent.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'Cairo Care RAG AI Agent NTI'))
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

class ChatRequest(BaseModel):
    message: str
    thread_id: str

@app.post("/chat")
async def chat_stream(request: ChatRequest):
    def event_generator():
        try:
            # Stream tokens from LangGraph agent
            for msg, metadata in agent.stream(
                {"messages": [{"role": "user", "content": request.message}]},
                config={"configurable": {"thread_id": request.thread_id}},
                stream_mode="messages",
            ):
                if msg.content and isinstance(msg.content, str):
                    # Hide internal tool calls that return ugly raw data (like get_user_coordinates)
                    # Stream all other ToolMessages because they contain beautifully formatted Arabic text
                    if msg.__class__.__name__ == "ToolMessage" and getattr(msg, "name", "") == "get_user_coordinates":
                        continue
                    
                    # Wrap token in JSON to safely handle newlines/special chars in SSE
                    yield f"data: {json.dumps({'token': msg.content})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        # Signal the end of the stream
        yield "data: [DONE]\n\n"

    # Return as Server-Sent Events (SSE)
    return StreamingResponse(event_generator(), media_type="text/event-stream")
