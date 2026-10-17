# AI-powered-Document-Intelligence-System-OKF-

OKF (Open Knowledge Finder) is a Python-based document ingestion and semantic-search project. It converts PDF documents into structured text chunks, enriches metadata using a locally hosted language model, and builds a multilingual vector index for searching document content.

The project supports text-based PDFs and scanned documents, including English and Tamil content.

## Features

- **PDF text extraction:** Uses PyMuPDF to extract text from text-based PDFs.
- **OCR for scanned PDFs:** Uses Tesseract OCR via `pytesseract` and renders PDF pages with Poppler via `pdf2image`.
- **English and Tamil support:** OCR can use Tesseract language data for English and Tamil.
- **Text chunking:** Splits extracted text into chunks and stores them as Markdown files with YAML frontmatter.
- **LLM-based metadata enrichment:** Uses Ollama with Llama 3.1 to generate descriptions, tags, and document-type classifications.
- **Multilingual semantic search:** Uses `intfloat/multilingual-e5-base` with Sentence Transformers to embed document chunks.
- **Vector retrieval:** Uses FAISS to retrieve the nearest chunk embeddings for a query.

## Project Structure

```text
OKF/
├── src/
│   ├── search.py
│   ├── pdf_to_okf.py
│   ├── pdf_to_okf_ocr.py
│   └── embed_chunks.py
├── input/                  # Source PDFs (local)
├── output/                 # Generated Markdown chunks
├── index/                  # Generated FAISS index and metadata
├── requirements.txt
├── README.md
└── .gitignore
```

The `input/`, `output/`, and `index/` folders represent the typical data workflow. Adjust these names to match your actual local configuration.

## Requirements
- Python
- Tesseract OCR
- Poppler utilities
- Ollama, if using LLM-based metadata enrichment

## Installation

### 1. Create a virtual environment

```bash
python -m venv okf_env
```

On Windows PowerShell, activate it:

```powershell
.\okf_env\Scripts\Activate.ps1
```

Install the Python dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For a reproducible setup, generate and review a dependency snapshot from your working environment:

```bash
python -m pip freeze > requirements.txt
```

## External Tools

### Tesseract OCR

Install Tesseract and ensure it is accessible through your system PATH, or configure its executable path in the OCR script.

For English and Tamil OCR, install the language data files:

- `eng.traineddata`
- `tam.traineddata`

Check the installed languages with:

```bash
tesseract --list-langs
```

The output should include `eng` and `tam` if both language packs are installed.

### Poppler

Install Poppler and make its utilities, including `pdfinfo`, available to `pdf2image`.

On Windows, configure the Poppler `bin` directory in your PATH or in the OCR script.

### Ollama

Install Ollama separately and download the model used by the metadata-enrichment workflow:

```bash
ollama pull llama3.1
```

Ensure the model tag matches the one configured in your Python script.

Ollama and its model files are not installed through `requirements.txt`.

## Workflow

Run these commands from the repository root, assuming your scripts use the corresponding default paths and do not require additional arguments.

### 1. Process text-based PDFs

```bash
python src/pdf_to_okf.py
```

Extracts text from PDFs, splits the text into chunks, and writes structured Markdown files. If LLM enrichment is enabled, the workflow can also generate metadata through Ollama.

### 2. Process scanned PDFs with OCR

```bash
python src/pdf_to_okf_ocr.py
```

Uses Poppler and Tesseract to render and OCR scanned PDF pages.

OCR quality depends on scan resolution, document layout, language data, and text quality. Large documents can take considerable time to process.

### 3. Build the embedding index

```bash
python src/embed_chunks.py
```

Reads generated Markdown chunks, removes YAML frontmatter from the text being embedded, creates embeddings with `intfloat/multilingual-e5-base`, and builds a FAISS index.

The current workflow writes:

- `index/index.faiss`
- `index/metadata.json`

These are generated artifacts and can generally be rebuilt from the source documents and chunks.

### 4. Search the index

```bash
python src/search.py
```

Enter a query when prompted. The search script embeds the query, retrieves the five nearest vectors from FAISS, and displays result metadata and a text preview.

Check the actual script configuration if your local paths or command-line arguments differ from these examples.

## Embeddings and Retrieval

OKF uses the `intfloat/multilingual-e5-base` model through Sentence Transformers. The model produces 768-dimensional embeddings.

FAISS performs inner-product search over normalized vectors, which is equivalent to cosine similarity when the vectors are normalized.

For E5 models, the recommended convention is:

- Prefix queries with `query: `
- Prefix document chunks with `passage: `

If these prefixes are introduced, rebuild the document embeddings and FAISS index, then use the query prefix during search. Do not change only the query side of an existing index.

Multilingual embeddings make cross-language retrieval possible, but do not guarantee that every English query will retrieve the correct Tamil passage. OCR errors, chunk boundaries, query wording, and embedding configuration can all affect results.

Retrieval accuracy should be measured using known queries and labelled relevant passages rather than inferred from similarity scores alone.

## LLM Integration

Ollama and Llama 3.1 are used for local LLM inference in the metadata-enrichment workflow.

The LLM can generate:

- Document descriptions
- Tags
- Document-type classifications

The resulting metadata is stored alongside the generated Markdown chunks. Structured-output parsing and error handling help manage malformed responses and inference failures.

## Current Scope and Future Work

### Implemented or developed

- PDF text extraction and scanned-document OCR workflows
- Markdown chunk generation with YAML metadata
- Local LLM-based metadata enrichment using Ollama and Llama 3.1
- Multilingual embeddings using Sentence Transformers
- FAISS-based top-five semantic retrieval

### Planned enhancements

- **Hybrid retrieval:** Combine FAISS semantic search with BM25 keyword retrieval.
- **Retrieval evaluation:** Measure Precision@5, Recall@5, MRR, and cross-language retrieval success using a labelled test set.
- **RAG question answering:** Pass retrieved passages to an LLM to generate answers grounded in document content, ideally with source citations.

The current search workflow retrieves and displays passages. Full LLM-generated, source-grounded question answering should be considered future work until that integration is implemented and evaluated.

## Data and Git Hygiene

Do not commit your virtual environment, private PDFs, generated chunk collections, local model files, or generated indexes by default.

Typical `.gitignore` entries include:

```gitignore
okf_env/
.venv/
venv/
__pycache__/
*.py[cod]
input/
output/
index/
models/
*.faiss
.env
*.log
```

Adjust these paths to match your project. Only share sample documents that you have permission to redistribute and that contain no sensitive information.

## Limitations

- OCR output may be noisy, especially for low-resolution scans and complex layouts.
- Retrieval quality has not been established by a formal benchmark unless separately evaluated.
- Similarity scores are not percentages of correctness.
- Hybrid retrieval and full RAG answer generation remain planned enhancements until implemented and tested.

## License

Add a license file before distributing the project publicly. Choose a license that reflects how you want others to use, modify, and redistribute your code.
