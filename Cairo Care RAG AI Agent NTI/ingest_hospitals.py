import pandas as pd
from vector_store import get_vector_store

CSV_PATH = "hospitals.csv"

def format_hospital_row(row) -> str:
    return (
        f"اسم المستشفى: {row['اسم المستشفى']}\n"
        f"العنوان التفصيلي: {row['العنوان التفصيلي']}\n"
        f"التخصص: {row['التخصص']}\n"
        f"رقم التليفون: {row['رقم التليفون']}\n"
        f"الموقع الإلكتروني: {row['الموقع الإلكتروني']}"
    )

def main():
    df = pd.read_csv(CSV_PATH, encoding="utf-8")

    vector_store = get_vector_store()  # uses your Ollama embeddings + Qdrant

    docs = []
    metadatas = []

    for _, row in df.iterrows():
        text = format_hospital_row(row)

        metadata = {
            "name": row["اسم المستشفى"],
            "address": row["العنوان التفصيلي"],
            "lat": float(row["خط العرض"]),
            "lon": float(row["خط الطول"]),
            "specialty": row["التخصص"],
            "phone": str(row["رقم التليفون"]),
            "website": row["الموقع الإلكتروني"],
        }

        docs.append(text)
        metadatas.append(metadata)

    vector_store.add_texts(texts=docs, metadatas=metadatas)

    print(f"Inserted {len(docs)} hospitals into Qdrant collection.")

if __name__ == "__main__":
    main()