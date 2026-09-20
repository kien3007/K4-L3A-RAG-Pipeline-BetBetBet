"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn (RecursiveCharacterTextSplitter).
    3. Embed chunks bằng OpenAI embedding (hoặc provider trong .env).
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk phải theo docs/MODULE_CONTRACTS.md. ID cần ổn định để
chạy lại pipeline không tạo dữ liệu trùng. Task 5 phải dùng chung embed_texts().
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI

from src.contracts import validate_document

# Load biến môi trường từ .env
load_dotenv()

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Tham số chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

# Cấu hình embedding theo provider
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
if EMBEDDING_PROVIDER == "openai":
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_DIM = 1536
elif EMBEDDING_PROVIDER == "gemini":
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
    EMBEDDING_DIM = 768
else:
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    EMBEDDING_DIM = 1024

COLLECTION_NAME = "rag_documents"


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Tạo embedding cho danh sách văn bản theo provider được cấu hình."""
    if not texts:
        return []

    provider = os.getenv("EMBEDDING_PROVIDER", EMBEDDING_PROVIDER).lower()

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment or .env")
        client = OpenAI(api_key=api_key)
        model = os.getenv("EMBEDDING_MODEL", EMBEDDING_MODEL)

        batch_size = 128
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            formatted_batch = [t.replace("\n", " ") for t in batch]
            response = client.embeddings.create(input=formatted_batch, model=model)
            all_embeddings.extend([item.embedding for item in response.data])
        return all_embeddings

    elif provider == "sentence_transformers":
        from sentence_transformers import SentenceTransformer

        model_name = os.getenv("EMBEDDING_MODEL", EMBEDDING_MODEL)
        model = SentenceTransformer(model_name)
        return model.encode(texts).tolist()

    elif provider == "gemini":
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment or .env")
        client = genai.Client(api_key=api_key)
        model = os.getenv("EMBEDDING_MODEL", EMBEDDING_MODEL)
        all_embeddings = []
        for text in texts:
            res = client.models.embed_content(model=model, contents=text)
            all_embeddings.append(res.embedding.values)
        return all_embeddings

    else:
        raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {provider}")


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _extract_doc_metadata(path: Path, content: str) -> dict:
    """Trích xuất metadata (source, title, doc_type, url) từ header markdown hoặc tên file."""
    doc_type = "legal" if "legal" in path.parts else "news"
    title = path.stem
    source = path.name
    url = None

    for line in content.splitlines():
        line_stripped = line.strip()
        if line_stripped.startswith("# ") and title == path.stem:
            extracted_title = line_stripped[2:].strip()
            if extracted_title:
                title = extracted_title
        elif line_stripped.startswith("**Source:**"):
            val = line_stripped.replace("**Source:**", "").strip()
            if val:
                source = val
                if val.startswith("http://") or val.startswith("https://"):
                    url = val

    return {
        "source": source,
        "title": title,
        "doc_type": doc_type,
        "url": url,
    }


def load_documents() -> list[dict]:
    """Đọc Markdown và trả về danh sách Document theo contract."""
    documents = []
    if not STANDARDIZED_DIR.exists():
        return documents

    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue

        relative_id = path.relative_to(STANDARDIZED_DIR).as_posix()
        metadata = _extract_doc_metadata(path, content)

        doc = {
            "id": relative_id,
            "content": content,
            "metadata": metadata,
        }
        validate_document(doc, require_chunk=False)
        documents.append(doc)

    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index theo contract."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for document in documents:
        split_texts = [
            t.strip()
            for t in splitter.split_text(document["content"])
            if t.strip()
        ]
        for index, text in enumerate(split_texts):
            chunk = {
                "id": f"{document['id']}::chunk-{index}",
                "content": text,
                "metadata": {
                    **document["metadata"],
                    "chunk_index": index,
                },
            }
            validate_document(chunk, require_chunk=True)
            chunks.append(chunk)

    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    texts = [chunk["content"] for chunk in chunks]
    vectors = embed_texts(texts)
    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector
    return chunks


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB."""
    if not chunks:
        return

    collection = get_collection()
    batch_size = 250

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        ids = [chunk["id"] for chunk in batch]
        documents = [chunk["content"] for chunk in batch]
        embeddings = [chunk["embedding"] for chunk in batch]
        # Chuyển đổi None trong metadata thành chuỗi rỗng để tương thích ChromaDB backend
        metadatas = [
            {k: ("" if v is None else v) for k, v in chunk["metadata"].items()}
            for chunk in batch
        ]
        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    print("Step 1: Loading documents from data/standardized/...")
    documents = load_documents()
    print(f"Loaded {len(documents)} documents.")

    print(f"Step 2: Chunking documents (CHUNK_SIZE={CHUNK_SIZE}, CHUNK_OVERLAP={CHUNK_OVERLAP})...")
    chunks = chunk_documents(documents)
    print(f"Generated {len(chunks)} chunks.")

    print(f"Step 3: Embedding chunks with {EMBEDDING_PROVIDER} ({EMBEDDING_MODEL})...")
    embedded_chunks = embed_chunks(chunks)
    print(f"Successfully embedded {len(embedded_chunks)} chunks.")

    print("Step 4: Upserting into ChromaDB (cosine distance)...")
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks successfully into ChromaDB collection '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    run_pipeline()
