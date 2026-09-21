from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

try:
    from src.backend.config import (
        OLLAMA_BASE_URL,
        OLLAMA_EMBEDDING_MODEL,
        QDRANT_COLLECTION,
        QDRANT_URL,
    )
except ImportError:
    from config import (
        OLLAMA_BASE_URL,
        OLLAMA_EMBEDDING_MODEL,
        QDRANT_COLLECTION,
        QDRANT_URL,
    )


def get_embeddings():
    """
    Connects LangChain to the embedding model already running in Ollama.

    This object will later convert:
    - hospital CSV records into vectors during ingestion
    - user questions into vectors during search
    """
    return OllamaEmbeddings(
        model=OLLAMA_EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL,
    )


def get_qdrant_client():
    """
    Connects Python to Qdrant running in Docker.
    """
    return QdrantClient(url=QDRANT_URL)


def collection_exists(client):
    """
    Returns True if the hospitals collection already exists in Qdrant.
    """
    collections = client.get_collections().collections

    return any(
        collection.name == QDRANT_COLLECTION
        for collection in collections
    )


def create_collection_if_missing(client, embeddings):
    """
    Creates the Qdrant hospitals collection only if it does not exist.

    The vector size is measured from the actual embedding model instead
    of being manually hardcoded.
    """
    if collection_exists(client):
        print(f"Collection '{QDRANT_COLLECTION}' already exists.")
        return

    sample_vector = embeddings.embed_query("اختبار")
    vector_size = len(sample_vector)

    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,
        ),
    )

    print(
        f"Created collection '{QDRANT_COLLECTION}' "
        f"with vector dimension {vector_size}."
    )


def get_vector_store():
    """
    Returns a LangChain Qdrant vector-store object.

    This function is used by:
    - ingest.py, to add hospital documents
    - agent.py, to search hospital documents
    """
    client = get_qdrant_client()
    embeddings = get_embeddings()

    create_collection_if_missing(client, embeddings)

    return QdrantVectorStore(
        client=client,
        collection_name=QDRANT_COLLECTION,
        embedding=embeddings,
    )


def reset_collection():
    """
    Deletes all hospital vectors and metadata, then creates a new empty
    hospitals collection.

    Use this only before a complete re-index of the CSV.
    """
    client = get_qdrant_client()

    if collection_exists(client):
        client.delete_collection(
            collection_name=QDRANT_COLLECTION
        )
        print(f"Deleted old collection '{QDRANT_COLLECTION}'.")

    embeddings = get_embeddings()

    create_collection_if_missing(
        client=client,
        embeddings=embeddings,
    )