"""Cairo Care RAG and Vector Store Package."""
from .vector_store import (
    get_embeddings,
    get_qdrant_client,
    get_vector_store,
    create_collection_if_missing,
)

__all__ = [
    "get_embeddings",
    "get_qdrant_client",
    "get_vector_store",
    "create_collection_if_missing",
]
