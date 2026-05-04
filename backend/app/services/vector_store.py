import os
import json
import logging
import uuid
import numpy as np
from typing import List, Dict, Any
import faiss
from app.config import settings

logger = logging.getLogger(__name__)

os.makedirs(settings.INDEXES_PATH, exist_ok=True)

EMBEDDING_DIM = 1536


def _safe_document_id(document_id: str) -> str:
    """Validate document_id is a UUID to prevent path traversal attacks."""
    try:
        return str(uuid.UUID(document_id))
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid document_id: {document_id!r}")


def create_and_save_index(
    document_id: str,
    chunks: List[Dict[str, Any]],
    embeddings: List[List[float]]
) -> None:
    """Create FAISS index and save to disk."""
    document_id = _safe_document_id(document_id)
    embeddings_array = np.array(embeddings, dtype='float32')

    if embeddings_array.shape[1] != EMBEDDING_DIM:
        raise ValueError(
            f"Embedding dimension mismatch: expected {EMBEDDING_DIM}, got {embeddings_array.shape[1]}"
        )

    index = faiss.IndexFlatL2(EMBEDDING_DIM)
    index.add(embeddings_array)

    index_path = os.path.join(settings.INDEXES_PATH, f"{document_id}.faiss")
    faiss.write_index(index, index_path)

    metadata = {
        "chunks": [
            {
                "index": i,
                "content": chunk["content"][:200],
                "full_content": chunk["content"],
                "page_number": chunk["page_number"],
                "token_count": chunk.get("token_count", 0),
                "chunk_id": chunk["id"]
            }
            for i, chunk in enumerate(chunks)
        ]
    }

    metadata_path = os.path.join(settings.INDEXES_PATH, f"{document_id}_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f)

    logger.info(f"Saved FAISS index for document {document_id}: {len(chunks)} chunks")


def load_index(document_id: str) -> tuple:
    """Load FAISS index and metadata from disk."""
    document_id = _safe_document_id(document_id)
    index_path = os.path.join(settings.INDEXES_PATH, f"{document_id}.faiss")
    metadata_path = os.path.join(settings.INDEXES_PATH, f"{document_id}_metadata.json")

    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS index not found for document {document_id}")

    index = faiss.read_index(index_path)

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    return index, metadata


def search_index(
    document_id: str,
    query_embedding: List[float],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """Search FAISS index for similar chunks."""
    document_id = _safe_document_id(document_id)
    index, metadata = load_index(document_id)

    query_array = np.array([query_embedding], dtype='float32')

    k = min(top_k, index.ntotal)
    distances, indices = index.search(query_array, k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        chunk_meta = metadata["chunks"][idx]
        similarity_score = float(1 / (1 + dist))
        results.append({
            "content": chunk_meta.get("full_content", chunk_meta["content"]),
            "page_number": chunk_meta["page_number"],
            "similarity_score": similarity_score,
            "chunk_id": chunk_meta.get("chunk_id", f"{document_id}#chunk_{idx}"),
            "preview": chunk_meta["content"]
        })

    return sorted(results, key=lambda x: x["similarity_score"], reverse=True)


def delete_index(document_id: str) -> None:
    """Delete FAISS index files for a document."""
    document_id = _safe_document_id(document_id)
    index_path = os.path.join(settings.INDEXES_PATH, f"{document_id}.faiss")
    metadata_path = os.path.join(settings.INDEXES_PATH, f"{document_id}_metadata.json")

    for path in [index_path, metadata_path]:
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"Deleted {path}")


def index_exists(document_id: str) -> bool:
    """Check if FAISS index exists for document."""
    document_id = _safe_document_id(document_id)
    index_path = os.path.join(settings.INDEXES_PATH, f"{document_id}.faiss")
    return os.path.exists(index_path)
