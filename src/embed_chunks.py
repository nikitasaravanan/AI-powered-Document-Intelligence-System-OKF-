from pathlib import Path
import json

import faiss
import numpy as np

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("intfloat/multilingual-e5-base")

def load_chunk(path):
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            text = parts[2]
    
    return text.strip()

chunk_files = sorted(Path("output").glob("*/*.md"))

texts = []
metadata = []

for chunk_file in chunk_files:
    text = load_chunk(chunk_file)
    texts.append(text)

    metadata.append({
        "path": str(chunk_file),
        "book": chunk_file.parent.name,
        "chunk": chunk_file.name
    })

embeddings = model.encode(
    texts,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True
)

dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)
index.add(embeddings.astype("float32"))
index_dir = Path("index")
index_dir.mkdir(exist_ok=True)

faiss.write_index(
    index,
    str(index_dir / "index.faiss")
)

with open(index_dir /"metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)
