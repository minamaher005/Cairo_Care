from vector_store import get_qdrant_client, get_vector_store

from config import QDRANT_COLLECTION


def main():
    # Calling get_vector_store() automatically creates the collection
    # if it does not already exist.
    get_vector_store()

    # Connect directly to Qdrant so we can confirm the result.
    client = get_qdrant_client()

    collection_info = client.get_collection(
        collection_name=QDRANT_COLLECTION
    )

    print("\nCollection created successfully.")
    print(f"Collection name: {QDRANT_COLLECTION}")
    print(f"Status: {collection_info.status}")
    print(f"Points stored: {collection_info.points_count}")


if __name__ == "__main__":
    main()