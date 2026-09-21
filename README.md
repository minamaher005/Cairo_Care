# 🩺 Cairo Care
### AI-Powered Medical Assistant & Emergency Hospital Routing for Greater Cairo

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![LangChain / LangGraph](https://img.shields.io/badge/LangGraph-ReAct%20Agent-orange.svg?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Qdrant](https://img.shields.io/badge/Vector%20DB-Qdrant-red.svg?logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![Ollama](https://img.shields.io/badge/Local%20LLM-Ollama-black.svg?logo=ollama&logoColor=white)](https://ollama.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📌 Executive Summary

**Cairo Care** is an agentic medical routing and healthcare discovery platform tailored specifically for residents and visitors of Greater Cairo, Egypt. By integrating **LangGraph-driven agentic reasoning**, **Qdrant vector search**, real-time **Vezeeta** medical scraping, and **dual-tier automatic geolocation detection**, Cairo Care eliminates the critical latency of finding healthcare services during emergencies and routine medical inquiries alike.

Users can describe symptoms, request specialized doctors, or find nearby medical facilities without manually specifying their district or street address.

---

## 🌟 Key Capabilities

### 1. 📍 Dual-Tier Automatic Geolocation Awareness
- **High-Precision Browser GPS**: Client-side HTML5 Geolocation bridge automatically captures user coordinates and transmits them directly to the backend.
- **Zero-Permission IP Fallback**: Immediate vicinity detection via public IP geolocation, ensuring location-aware context on the very first page load without awaiting permission dialogs.
- **Cairo District Normalization Engine**: Proprietary mapping system supporting 40+ suburbs and historic neighborhoods (e.g., *El-Ashmawy, Bab El-Shaariya, El-Zaytoun, Maadi, New Cairo / 5th Settlement, Dokki, Mohandessin, Sheikh Zayed, 6th of October*) to canonical administrative zones and Vezeeta search slugs.
- **Manual District Override**: Sidebar quick-picker with 15 major Greater Cairo districts and single-click update.

### 2. 🚑 Emergency Routing & Vector RAG (Qdrant)
- Semantic vector search indexing Cairo hospitals and clinics (`cairo_hospitals_enriched.csv`).
- **Autonomous Emergency Protocol**: Detects life-threatening symptoms (acute chest pain, stroke signs, severe hemorrhage, trauma) and instantly dispatches the nearest emergency room matching user coordinates alongside Egypt's emergency hotline (`123`), bypassing unnecessary questions.

### 3. 👨‍⚕️ Real-Time Doctor Discovery (Vezeeta)
- Live programmatic integration with **Vezeeta** to search for certified practitioners, clinics, and consultation fees.
- Automated extraction and mapping of medical specialties (Cardiology, Orthopedics, Pediatrics, Neurology, Dermatology, etc.) paired with the user's localized district slug.

### 4. 🧠 Agentic Reasoning with LangGraph
- Multi-tool ReAct supervisor graph orchestrating:
  - `find_nearest_hospitals`: Qdrant vector retrieval.
  - `get_doctors`: Live Vezeeta query engine.
  - `reverse_geocode_location`: LocationIQ reverse geocoder tool.
- Persistent session checkpointer for seamless multi-turn context retention.
- Token-by-token Server-Sent Events (SSE) streaming for real-time responsiveness.

### 5. 🎨 Modern Glassmorphic UI
- Built with Streamlit featuring a customized dark theme, glassmorphism tokens, and responsive Arabic typography (`Noto Kufi Arabic` + `Figtree`).
- Sidebar session manager supporting conversation switching, relative timestamps, and thread deletion.
- Live status indicators showing current detected location, accuracy source (`GPS`, `IP`, `Manual`), and model readiness.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    User([👤 User / Web Client])

    subgraph FrontendLayer [🖥️ Streamlit Frontend Layer]
        UI[Glassmorphic UI & Markdown Parser]
        GeoBridge[HTML5 Geolocation Bridge]
        PresetSelector[Cairo District Selector & Session History]
    end

    subgraph APILayer [⚡ FastAPI Backend Service]
        ChatEndpoint[/chat & /chat/stream SSE]
        LocEndpoints[/api/location/browser & /ip & /resolve]
        ThreadRegistry[In-Memory Thread & Checkpoint Registry]
    end

    subgraph AgentCore [🤖 LangGraph ReAct Agent]
        Supervisor[Cairo Care Agent Supervisor]
        HospTool[find_nearest_hospitals Tool]
        DocTool[get_doctors Tool]
        GeoTool[reverse_geocode_location Tool]
    end

    subgraph DataIntegrations [🗄️ Knowledge Base & External APIs]
        Qdrant[(Qdrant Vector Database - Cairo Hospitals)]
        Ollama[[Local LLM - Ollama Engine]]
        VezeetaAPI[(Vezeeta Provider Directory)]
        LocationIQ[(LocationIQ Geocoding API)]
    end

    User <-->|Prompts & Coordinates| UI
    GeoBridge -->|POST /api/location/browser| LocEndpoints
    UI <-->|SSE Stream & Location Payload| ChatEndpoint
    ChatEndpoint --> Supervisor
    Supervisor <--> Ollama
    Supervisor --> HospTool <--> Qdrant
    Supervisor --> DocTool <--> VezeetaAPI
    Supervisor --> GeoTool <--> LocationIQ
```

---

## 📁 Repository Layout

```text
Cairo_Care/
├── src/
│   ├── backend/                 # FastAPI server, LangGraph agent, and configurations
│   │   ├── app.py               # Main FastAPI API with SSE streaming & geolocation routes
│   │   ├── agent.py             # LangGraph ReAct Agent with location awareness
│   │   ├── config.py            # Ollama & Qdrant configuration
│   │   ├── state.py             # Agent conversation state schema
│   │   ├── tools/               # Agent tool implementations
│   │   │   ├── location_tools.py# Reverse geocoding & Cairo district matcher
│   │   │   ├── vezeeta_tool.py  # Vezeeta doctor scraper tool
│   │   │   └── vzeeta.py        # Vezeeta client & HTML parser
│   │   └── rag/                 # Vector store retrieval & ingestion
│   │       ├── vector_store.py  # Qdrant client connection & hybrid search
│   │       ├── ingest_hospitals.py # Ingestion pipeline
│   │       └── create_collection.py# Qdrant collection setup
│   │
│   └── frontend/                # Streamlit user interface
│       ├── app.py               # Unified modern glassmorphic Streamlit application
│       └── .streamlit/
│           └── config.toml
│
├── data/                        # Datasets (cairo_hospitals_enriched.csv, hospitals.csv)
├── docs/                        # Project documentation guides (.mdx files)
├── tests/                       # Test suite (test_components.py)
│
├── Backend.py                   # Root runner (starts FastAPI backend)
├── frontend.py                  # Root runner (starts Streamlit frontend)
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Qdrant Docker Compose file
├── .env                         # Environment variables
├── .gitignore                   # Git ignore rules
└── README.md                    # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10 or higher**
- **Ollama** installed with a multilingual language model (e.g. `llama3`, `qwen2.5`, or `mistral`):
  ```bash
  ollama run llama3
  ```
- **Qdrant** vector database (running locally or via Docker):
  ```bash
  docker compose up -d
  # or: docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant
  ```

### 2. Installation
Clone this repository and install all required packages:
```bash
git clone https://github.com/your-username/Cairo_Care.git
cd Cairo_Care
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the project root:
```env
# Optional: Higher-quota LocationIQ API key for reverse geocoding
LOCATIONIQ_API_KEY=your_locationiq_api_key_here

# Ollama & Qdrant endpoints (defaults)
OLLAMA_BASE_URL=http://localhost:11434
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### 4. Initialize Vector Store
If running Qdrant for the first time, initialize and populate the collection:
```bash
python -m src.backend.rag.create_collection
python -m src.backend.rag.ingest_hospitals
```

### 5. Running the Application

#### Step A: Launch FastAPI Backend
```bash
# Option 1: Root entrypoint
uvicorn Backend:app --reload --port 8000

# Option 2: Direct module
uvicorn src.backend.app:app --reload --port 8000
```

#### Step B: Launch Streamlit Frontend
In a separate terminal window:
```bash
streamlit run frontend.py
```
Access the application in your browser at `http://localhost:8501`.

---

## 🔌 API Reference

| Method | Route | Description | Payload / Parameters |
|---|---|---|---|
| `POST` | `/chat` | Main SSE streaming endpoint with location context injection | `{"message": str, "thread_id": str, "user_location": dict}` |
| `POST` | `/chat/stream` | Alternate SSE streaming endpoint | `{"message": str, "thread_id": str, "user_location": dict}` |
| `POST` | `/api/location/browser` | Ingests client GPS coordinates from HTML5 Geolocation | `{"thread_id": str, "lat": float, "lon": float}` |
| `GET` | `/api/location/browser/{thread_id}` | Retrieves stored GPS data for a given session | `thread_id: path parameter` |
| `GET` | `/api/location/ip` | Resolves approximate location from public IP | None |
| `POST` | `/api/location/resolve` | Translates raw coordinates into Cairo district name & Vezeeta slug | `{"lat": float, "lon": float}` |
| `GET` | `/threads` | Returns list of historical chat threads | None |
| `GET` | `/threads/{thread_id}/messages`| Returns full message history for a thread | `thread_id: path parameter` |
| `DELETE` | `/threads/{thread_id}` | Deletes a conversation thread and its checkpoints | `thread_id: path parameter` |

---

## 💬 Sample User Queries

- **Critical Emergency**:
  > *"I feel severe squeezing chest pain and shortness of breath."*  
  > ➡️ **Agent Action**: Bypasses conversational questions. Dispatches the closest cardiac emergency facility matching detected coordinates, emergency room contact, and advises calling **123**.

- **Localized Doctor Inquiry**:
  > *"I need an experienced pediatrician."*  
  > ➡️ **Agent Action**: Detects current vicinity (e.g. *Maadi* / `المعادي`), queries Vezeeta for pediatricians in that specific district, and displays top matches with specialties, clinics, and ratings.

- **Explicit District Override**:
  > *"Find me orthopedic clinics in Heliopolis (Masr El-Gedida)."*  
  > ➡️ **Agent Action**: Respects user's explicit request and searches within *Heliopolis* regardless of current GPS position.

---

## ⚠️ Medical & Legal Disclaimer

> **IMPORTANT NOTICE:**  
> **Cairo Care** is an artificial intelligence application intended for triage assistance, informational guidance, and healthcare navigation. **It does not provide formal medical diagnosis, clinical prognosis, or direct medical treatment.** In the event of a medical emergency or life-threatening situation, immediately contact the Egyptian Ambulance Organization at **123** or proceed to the nearest hospital emergency room.

---

## 📄 License

This project is licensed under the **MIT License** - see the `LICENSE` file for details.
