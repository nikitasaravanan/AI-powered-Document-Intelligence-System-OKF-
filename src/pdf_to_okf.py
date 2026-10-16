#turn to okf format
#and generates the chunks

import fitz
import re
import json
import requests
import yaml
import string

from pathlib import Path
from datetime import datetime


def extract_text(path):
    doc = fitz.open(path)

    pages = []
    for page in doc:
        pages.append(page.get_text())

    return "\n".join(pages)

def get_paragraphs(text):
    paragraphs = re.split(r"\n\s*\n", text)

    paras = [
        p.strip()
        for p in paragraphs
        if len(p.strip()) > 50
    ]

    return paras

#ollama enrichment
def safe_json_parse(raw):
    try:
        return json.loads(raw)
    except:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])

def enrich_metadata_local(sample_text):
    prompt = f"""
    Extract structured metadata from this document.

    Return ONLY valid JSON with:
    - description (1-2 sentences)
    - tags (5-10 keywords)
    - document_type
    
    TEXT:
    {sample_text}
    """
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.1",
            "prompt": prompt,
            "stream": False
        }
    )

    raw = response.json().get("response", "")
    if not raw.strip():
        raise ValueError("Empty response from Ollama")

    return safe_json_parse(raw)

def chunk_paragraphs(text, max_chars=1500):
    paragraphs = get_paragraphs(text)

    chunks = []
    current_chunk = []

    current_size = 0

    for paragraph in paragraphs:

        para_size = len(paragraph)

        if current_size + para_size > max_chars and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [paragraph]
            current_size = para_size

        else:
            current_chunk.append(paragraph)
            current_size += para_size

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks

def process_pdf(pdf_file, output_dir, text):
    paragraphs = get_paragraphs(text)
    if not paragraphs:
        print(f"Skipping {pdf_file} due to no valid paragraphs found.")
        return
    
    first_paragraph = paragraphs[0] 
    #last_paragraph = extract_last_paragraph(text)

    chunks = chunk_paragraphs(text)

    # Use the first substantial chunk
    sample_text = next(
        (chunk for chunk in chunks if len(chunk) > 1000),
        chunks[0]
    )
    description = ""
    llm_data = {}

    try:
        llm_data = enrich_metadata_local(sample_text)
        description = "".join(llm_data.get("description", "").split())
    except Exception as e:
        print(f"Ollama failed for {pdf_file.name}, fallback used:", e)

    metadata = {
        "title": pdf_file.stem.strip(),
        "author": "",
        "source_file": pdf_file.name,
        "description": description or first_paragraph[:500],
        "tags": llm_data.get("tags", []),
        "document_type": llm_data.get("document_type", ""),
        "timestamp": datetime.utcnow().isoformat()
    }

    book_output_dir = output_dir / pdf_file.stem.strip()
    book_output_dir.mkdir(exist_ok=True)

    for idx, chunk in enumerate(chunks, start=1):

        chunk_metadata = metadata.copy()

        chunk_metadata["chunk_id"] = idx
        chunk_metadata["chunk_count"] = len(chunks)
        chunk_metadata["chunk_size"] = len(chunk)

        yaml_block = (
            "---\n"
            + yaml.dump(
                chunk_metadata,
                allow_unicode=True,
                sort_keys=False
            )
            + "---\n\n"
        )

        content = yaml_block + chunk

        chunk_file = book_output_dir / f"chunk_{idx:04d}.md"

        chunk_file.write_text(
            content,
            encoding="utf-8"
        )

    print(f"Processed {pdf_file.name}: "
    f"{len(chunks)} chunks created")

def is_english_document(text, threshold=0.70):
    """
    Returns True if the text appears to be primarily English.
    """
    if not text:
        return False

    sample = text[:5000]

    english_chars = sum(
        c in string.ascii_letters + string.digits + string.whitespace + string.punctuation
        for c in sample
    )

    ratio = english_chars / len(sample)

    return ratio >= threshold

def main():
    input_dir = Path(r"D:\EBook_OKF")
    output_dir = Path("output")

    output_dir.mkdir(exist_ok=True)

    for pdf_file in input_dir.rglob("*"):

        if not (pdf_file.is_file() and pdf_file.suffix.lower() == ".pdf"):
            continue

        book_output_dir = output_dir / pdf_file.stem.strip()

        # Skip if already processed
        if book_output_dir.exists() and any(book_output_dir.glob("chunk_*.md")):
            print(f"Skipping (already processed): {pdf_file.name}")
            continue

        try:
            # Extract text only once
            text = extract_text(pdf_file)

            # Skip if not primarily English
            if not is_english_document(text):
                print(f"Skipping (not English): {pdf_file.name}")
                continue

            print(f"Processing: {pdf_file.name}")

            process_pdf(pdf_file, output_dir, text)

        except Exception as e:
            print(f"Failed: {pdf_file}")
            print(e)

if __name__ == "__main__":
    main()