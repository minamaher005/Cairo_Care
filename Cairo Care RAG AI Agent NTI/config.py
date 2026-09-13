import os
from dotenv import load_dotenv

# Load values from the .env file in this project folder.
load_dotenv()

# Ollama configuration
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434",
)

OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL")

# Qdrant configuration
QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "http://localhost:6333",
)

QDRANT_COLLECTION = os.getenv(
    "QDRANT_COLLECTION",
    "hospitals",
)

# Stop immediately with a clear error if a required model name is missing.
if not OLLAMA_LLM_MODEL:
    raise ValueError(
        "OLLAMA_LLM_MODEL is missing. Check your .env file."
    )

if not OLLAMA_EMBEDDING_MODEL:
    raise ValueError(
        "OLLAMA_EMBEDDING_MODEL is missing. Check your .env file."
    )