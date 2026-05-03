from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_pages(
    pages: List[Dict[str, Any]],
    document_id: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50
) -> List[Dict[str, Any]]:
    """Chunk page content with metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size * 4,
        chunk_overlap=chunk_overlap * 4,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len
    )

    chunks = []
    chunk_index = 0

    for page in pages:
        page_chunks = splitter.split_text(page["content"])
        for chunk_content in page_chunks:
            if not chunk_content.strip():
                continue
            token_count = len(chunk_content) // 4
            chunks.append({
                "id": f"{document_id}#chunk_{chunk_index}",
                "content": chunk_content,
                "page_number": page["page_number"],
                "chunk_index": chunk_index,
                "token_count": token_count
            })
            chunk_index += 1

    return chunks
