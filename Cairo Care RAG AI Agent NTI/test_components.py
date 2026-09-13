import requests

from langchain_ollama import ChatOllama, OllamaEmbeddings
from qdrant_client import QdrantClient

from config import (
    OLLAMA_BASE_URL,
    OLLAMA_LLM_MODEL,
    OLLAMA_EMBEDDING_MODEL,
    QDRANT_URL,
)


def test_ollama_server():
    """
    Checks whether the Ollama service is running and prints
    all local models Ollama can see.
    """
    response = requests.get(
        f"{OLLAMA_BASE_URL}/api/tags",
        timeout=10,
    )
    response.raise_for_status()

    models = response.json().get("models", [])

    print("Ollama server: OK")
    print("Models available in Ollama:")

    for model in models:
        print(f" - {model['name']}")


def test_embedding_model():
    """
    Sends Arabic text to BGE-M3 through Ollama and checks
    that it returns a vector.
    """
    embeddings = OllamaEmbeddings(
        model=OLLAMA_EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL,
    )

    test_text = "مستشفى قلب في مدينة نصر"
    vector = embeddings.embed_query(test_text)

    print("\nEmbedding model: OK")
    print(f"Embedding model: {OLLAMA_EMBEDDING_MODEL}")
    print(f"Test text: {test_text}")
    print(f"Vector dimension: {len(vector)}")
    print(f"First 5 vector values: {vector[:5]}")


def test_llm():
    """
    Sends a very small Arabic prompt to your local Qwen model.
    """
    llm = ChatOllama(
        model=OLLAMA_LLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0,
    )

    response = llm.invoke(
        "أجب بكلمة واحدة فقط: هل أنت جاهز؟"
    )

    print("\nLLM: OK")
    print(f"LLM model: {OLLAMA_LLM_MODEL}")
    print(f"LLM response: {response.content}")


def test_qdrant():
    """
    Checks whether Python can connect to the Qdrant Docker container.
    """
    client = QdrantClient(url=QDRANT_URL)
    collections = client.get_collections()

    print("\nQdrant: OK")
    print(f"Qdrant URL: {QDRANT_URL}")
    print(f"Number of collections: {len(collections.collections)}")


def main():
    print("=" * 60)
    print("Testing local Hospital RAG components")
    print("=" * 60)

    test_ollama_server()
    test_embedding_model()
    test_llm()
    test_qdrant()

    print("\n" + "=" * 60)
    print("All component tests completed.")
    print("=" * 60)


if __name__ == "__main__":
    main()