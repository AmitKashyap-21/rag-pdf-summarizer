import time
import logging
from typing import List, Dict, Any, Optional
from app.services.openrouter import openrouter_service
from app.services.vector_store import search_index, index_exists

logger = logging.getLogger(__name__)


async def summarize_document(
    document_id: str,
    level: str = "medium",
    custom_prompt: Optional[str] = None,
    model: str = "openai/gpt-3.5-turbo",
    top_k: int = 10
) -> Dict[str, Any]:
    """Retrieve top chunks and summarize using LLM."""
    start_time = time.time()

    if not index_exists(document_id):
        raise FileNotFoundError(f"No index found for document {document_id}")

    # Use a generic query to get representative chunks for summarization
    query_text = "main topics key points important information summary"
    query_embeddings = await openrouter_service.embed([query_text])
    query_embedding = query_embeddings[0]

    chunks = search_index(document_id, query_embedding, top_k=top_k)

    context = "\n\n".join([
        f"[Page {c['page_number']}]\n{c['content']}"
        for c in chunks
    ])

    result = await openrouter_service.summarize(
        context=context,
        level=level,
        custom_prompt=custom_prompt,
        model=model
    )

    generation_time_ms = int((time.time() - start_time) * 1000)

    return {
        **result,
        "summary_level": level,
        "chunks_used": [
            {
                "chunk_id": c["chunk_id"],
                "page_number": c["page_number"],
                "similarity_score": c["similarity_score"],
                "preview": c["preview"][:100]
            }
            for c in chunks
        ],
        "generation_time_ms": generation_time_ms
    }
