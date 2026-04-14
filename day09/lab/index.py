import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CẤU HÌNH
# =============================================================================

DOCS_DIR = Path(__file__).parent / "data" / "docs"
CHROMA_DB_DIR = Path(__file__).parent / "chroma_db"

# TODO Sprint 1: Điều chỉnh chunk size và overlap theo quyết định của nhóm
# Gợi ý từ slide: chunk 300-500 tokens, overlap 50-80 tokens
CHUNK_SIZE = 400       # tokens (ước lượng bằng số ký tự / 4)
CHUNK_OVERLAP = 80     # tokens overlap giữa các chunk


# =============================================================================
# STEP 1: PREPROCESS
# Làm sạch text trước khi chunk và embed
# =============================================================================

def preprocess_document(raw_text: str, filepath: str) -> Dict[str, Any]:
    """
    Sử dụng Regex để bóc tách Metadata và làm sạch Body text.
    """
    metadata_regex = {
        "source": r"Source:\s*(.*)",
        "department": r"Department:\s*(.*)",
        "effective_date": r"Effective Date:\s*(.*)",
        "access": r"Access:\s*(.*)"
    }
    
    metadata = {
        "source": Path(filepath).name,
        "department": "unknown",
        "effective_date": "unknown",
        "access": "internal"
    }

    # Tìm ranh giới giữa Header và Body (dựa trên sự xuất hiện của Section đầu tiên hoặc dòng trống sau meta)
    parts = re.split(r"(?=== )", raw_text, maxsplit=1)
    header_raw = parts[0]
    body_raw = parts[1] if len(parts) > 1 else raw_text

    for key, pattern in metadata_regex.items():
        match = re.search(pattern, header_raw, re.IGNORECASE)
        if match:
            metadata[key] = match.group(1).strip()

    # Làm sạch body: xóa khoảng trắng thừa, chuẩn hóa xuống dòng
    cleaned_body = body_raw.strip()
    cleaned_body = re.sub(r"\n{3,}", "\n\n", cleaned_body)

    return {
        "text": cleaned_body,
        "metadata": metadata,
    }


# =============================================================================
# STEP 2: CHUNK
# Chia tài liệu thành các đoạn nhỏ theo cấu trúc tự nhiên
# =============================================================================

def chunk_document(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Smart Chunking: ưu tiên cắt theo Section, sau đó theo Paragraph.
    """
    text = doc["text"]
    base_metadata = doc["metadata"].copy()
    chunks = []

    # Split theo Section heading "=== ... ==="
    # Dùng regex split nhưng giữ lại delimiter để biết tên section
    parts = re.split(r"(===.*?===)", text)
    
    current_section = "General"
    for i in range(len(parts)):
        part = parts[i].strip()
        if not part: continue
        
        if re.match(r"===.*?===", part):
            current_section = part.strip("= ").strip()
        else:
            # Đây là nội dung của section
            section_chunks = _split_by_size(
                part, 
                base_metadata, 
                current_section
            )
            chunks.extend(section_chunks)

    return chunks


def _split_by_size(
    text: str,
    base_metadata: Dict,
    section: str,
    max_chars: int = 1500, # Ngưỡng tối ưu (~400 tokens)
    overlap_chars: int = 300,
) -> List[Dict[str, Any]]:
    """
    Cắt nhỏ nội dung dài theo Paragraph đảm bảo ngữ cảnh.
    """
    if len(text) <= max_chars:
        return [{
            "text": f"Section: {section}\n{text}",
            "metadata": {**base_metadata, "section": section}
        }]

    # Chia theo đoạn văn trước
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk_text = f"Section: {section}\n"
    
    for p in paragraphs:
        if len(current_chunk_text) + len(p) < max_chars:
            current_chunk_text += p + "\n\n"
        else:
            # Lưu chunk hiện tại
            chunks.append({
                "text": current_chunk_text.strip(),
                "metadata": {**base_metadata, "section": section}
            })
            # Bắt đầu chunk mới với overlap (lấy 1 đoạn văn trước đó nếu có thể)
            current_chunk_text = f"Section: {section} (tiếp)\n{p}\n\n"

    # Add last chunk
    if current_chunk_text.strip():
        chunks.append({
            "text": current_chunk_text.strip(),
            "metadata": {**base_metadata, "section": section}
        })

    return chunks


# =============================================================================
# STEP 3: EMBED + STORE
# Embed các chunk và lưu vào ChromaDB
# =============================================================================

# Load model globally to avoid reloading in κάθε call
_embed_model = None

def get_embedding(text: str, task: str = "retrieval.passage") -> List[float]:
    """
    Tạo embedding vector bằng Jina AI API (Model: jina-embeddings-v5-text-small).
    """
    import requests
    api_key = os.getenv("JINA_API_KEY")
    if not api_key:
        raise ValueError("Missing JINA_API_KEY in .env file")
    
    url = "https://api.jina.ai/v1/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": "jina-embeddings-v5-text-small",
        "task": task,
        "dimensions": 1024,
        "input": [text]
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()['data'][0]['embedding']
    else:
        raise Exception(f"Jina API Error: {response.status_code} - {response.text}")


def build_index(docs_dir: Path = DOCS_DIR, db_dir: Path = CHROMA_DB_DIR) -> None:
    """
    Pipeline hoàn chỉnh sử dụng Jina AI Embeddings.
    """
    import chromadb

    print(f"Đang build index từ: {docs_dir}")
    db_dir.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(db_dir))
    collection = client.get_or_create_collection(
        name="rag_lab",
        metadata={"hnsw:space": "cosine"}
    )

    total_chunks = 0
    doc_files = list(docs_dir.glob("*.txt"))

    if not doc_files:
        print(f"Không tìm thấy file .txt trong {docs_dir}")
        return

    for filepath in doc_files:
        print(f"  Processing: {filepath.name}")
        raw_text = filepath.read_text(encoding="utf-8")

        doc = preprocess_document(raw_text, str(filepath))
        chunks = chunk_document(doc)
        
        ids = []
        embeddings = []
        documents = []
        metadatas = []

        print(f"    → Đang tạo embedding cho {len(chunks)} chunks...")
        for i, chunk in enumerate(chunks):
            chunk_id = f"{filepath.stem}_{i}"
            # Sử dụng task retrieval.passage cho indexing
            embedding = get_embedding(chunk["text"], task="retrieval.passage")
            
            ids.append(chunk_id)
            embeddings.append(embedding)
            documents.append(chunk["text"])
            metadatas.append(chunk["metadata"])
            
        if ids:
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
            total_chunks += len(ids)

    print(f"\nHoàn thành! Tổng số chunks đã index: {total_chunks}")


# =============================================================================
# STEP 4: INSPECT / KIỂM TRA
# Dùng để debug và kiểm tra chất lượng index
# =============================================================================

def list_chunks(db_dir: Path = CHROMA_DB_DIR, n: int = 5) -> None:
    """
    In ra n chunk đầu tiên trong ChromaDB để kiểm tra chất lượng index.

    TODO Sprint 1:
    Implement sau khi hoàn thành build_index().
    Kiểm tra:
    - Chunk có giữ đủ metadata không? (source, section, effective_date)
    - Chunk có bị cắt giữa điều khoản không?
    - Metadata effective_date có đúng không?
    """
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(db_dir))
        collection = client.get_collection("rag_lab")
        results = collection.get(limit=n, include=["documents", "metadatas"])

        print(f"\n=== Top {n} chunks trong index ===\n")
        for i, (doc, meta) in enumerate(zip(results["documents"], results["metadatas"])):
            print(f"[Chunk {i+1}]")
            print(f"  Source: {meta.get('source', 'N/A')}")
            print(f"  Section: {meta.get('section', 'N/A')}")
            print(f"  Effective Date: {meta.get('effective_date', 'N/A')}")
            print(f"  Text preview: {doc[:120]}...")
            print()
    except Exception as e:
        print(f"Lỗi khi đọc index: {e}")
        print("Hãy chạy build_index() trước.")


def inspect_metadata_coverage(db_dir: Path = CHROMA_DB_DIR) -> None:
    """
    Kiểm tra phân phối metadata trong toàn bộ index.

    Checklist Sprint 1:
    - Mọi chunk đều có source?
    - Có bao nhiêu chunk từ mỗi department?
    - Chunk nào thiếu effective_date?

    TODO: Implement sau khi build_index() hoàn thành.
    """
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(db_dir))
        collection = client.get_collection("rag_lab")
        results = collection.get(include=["metadatas"])

        print(f"\nTổng chunks: {len(results['metadatas'])}")

        # TODO: Phân tích metadata
        # Đếm theo department, kiểm tra effective_date missing, v.v.
        departments = {}
        missing_date = 0
        for meta in results["metadatas"]:
            dept = meta.get("department", "unknown")
            departments[dept] = departments.get(dept, 0) + 1
            if meta.get("effective_date") in ("unknown", "", None):
                missing_date += 1

        print("Phân bố theo department:")
        for dept, count in departments.items():
            print(f"  {dept}: {count} chunks")
        print(f"Chunks thiếu effective_date: {missing_date}")

    except Exception as e:
        print(f"Lỗi: {e}. Hãy chạy build_index() trước.")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Sprint 1: Build RAG Index")
    print("=" * 60)

    # Bước 1: Kiểm tra docs
    doc_files = list(DOCS_DIR.glob("*.txt"))
    print(f"\nTìm thấy {len(doc_files)} tài liệu:")
    for f in doc_files:
        print(f"  - {f.name}")

    # Bước 2: Test preprocess và chunking (không cần API key)
    print("\n--- Test preprocess + chunking ---")
    for filepath in doc_files[:1]:  # Test với 1 file đầu
        raw = filepath.read_text(encoding="utf-8")
        doc = preprocess_document(raw, str(filepath))
        chunks = chunk_document(doc)
        print(f"\nFile: {filepath.name}")
        print(f"  Metadata: {doc['metadata']}")
        print(f"  Số chunks: {len(chunks)}")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n  [Chunk {i+1}] Section: {chunk['metadata']['section']}")
            print(f"  Text: {chunk['text'][:150]}...")

    # Bước 3: Build index (yêu cầu implement get_embedding)
    print("\n--- Build Full Index ---")
    # Uncomment dòng dưới sau khi implement get_embedding():
    build_index()

    # Bước 4: Kiểm tra index
    # Uncomment sau khi build_index() thành công:
    list_chunks()
    inspect_metadata_coverage()
