from pathlib import Path
import json
import yaml

import faiss
from sentence_transformers import SentenceTransformer

def load_chunk_with_metadata(path):
    text = path.read_text(encoding="utf-8")

    metadata = {}
    content = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            metadata = yaml.safe_load(parts[1]) or {}
            content = parts[2].strip()

    return metadata, content

def make_preview(text, query, window=200):
    lower_text = text.lower()
    lower_query = query.lower()

    pos = lower_text.find(lower_query)

    if pos == -1:
        preview = text[:2 * window]
        if len(text) > 2 * window:
            preview += "..."
        return preview.replace("\n", " ")

    start = max(0, pos - window)
    end = min(len(text), pos + len(query) + window)

    preview = text[start:end]
    if start > 0:
        preview = "..." + preview
    if end < len(text):
        preview += "..."

    return preview.replace("\n", " ")

model = SentenceTransformer("intfloat/multilingual-e5-base")

index = faiss.read_index(str("index/index.faiss"))

with open("index/metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

query = input("Search: ").strip()
query_embedding = model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype("float32")

k = 5
distances, indices = index.search(query_embedding, k)

for rank, idx in enumerate(indices[0], start=1):

    item = metadata[idx]
    score = distances[0][rank - 1]

    chunk_path = Path(item["path"])

    chunk_metadata, text = load_chunk_with_metadata(chunk_path)

    preview = make_preview(text, query)

    print("=" * 80)
    print(f"Result       : {rank}")
    print(f"Similarity   : {score:.4f}")
    print()

    print(f"Title        : {chunk_metadata.get('title', '')}")
    print(f"Type         : {chunk_metadata.get('document_type', '')}")
    print(f"Author       : {chunk_metadata.get('author', '')}")
    print(f"Source       : {chunk_metadata.get('source_file', '')}")

    print(
        f"Chunk        : "
        f"{chunk_metadata.get('chunk_id', '?')}/"
        f"{chunk_metadata.get('chunk_count', '?')}"
    )

    tags = chunk_metadata.get("tags", [])

    if tags:
        print("Tags         :", ", ".join(tags))

    print("-" * 80)
    print(preview)

    if len(text) > 500:
        print("...")

    print("=" * 80)