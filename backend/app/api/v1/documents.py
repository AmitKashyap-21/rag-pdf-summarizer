import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.document import Document, TokenUsageLog
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    UploadResponse,
    SummarizeRequest,
    SummaryResponse,
    QueryRequest,
    QueryResponse,
)
from app.services.pdf_processor import extract_text_from_pdf, get_page_count
from app.services.chunker import chunk_pages
from app.services.openrouter import openrouter_service
from app.services.vector_store import (
    create_and_save_index,
    search_index,
    delete_index,
    index_exists,
)
from app.services.summarizer import summarize_document
from app.middleware.auth import verify_api_key
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/documents/upload", response_model=UploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    results = []
    errors = []

    for file in files:
        try:
            content = await file.read()

            if content[:4] != b'%PDF':
                errors.append({"error": "Not a valid PDF", "file": file.filename})
                continue

            max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
            if len(content) > max_size:
                errors.append({
                    "error": f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit",
                    "code": "FILE_TOO_LARGE",
                    "file": file.filename
                })
                continue

            pages = extract_text_from_pdf(content)
            num_pages = get_page_count(content)

            doc = Document(
                filename=file.filename,
                file_size=len(content),
                num_pages=num_pages,
                num_chunks=0,
                status="processing"
            )
            db.add(doc)
            await db.commit()
            await db.refresh(doc)

            try:
                chunks = chunk_pages(pages, str(doc.id), settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)

                chunk_texts = [c["content"] for c in chunks]
                embeddings = await openrouter_service.embed_in_batches(chunk_texts)

                create_and_save_index(str(doc.id), chunks, embeddings)

                doc.num_chunks = len(chunks)
                doc.status = "ready"
                await db.commit()
                await db.refresh(doc)

                results.append(DocumentResponse.model_validate(doc))

            except Exception as e:
                logger.error(f"Processing failed for {file.filename}: {e}")
                doc.status = "failed"
                doc.error_message = str(e)
                await db.commit()
                errors.append({"error": str(e), "file": file.filename})

        except Exception as e:
            logger.error(f"Upload failed for {file.filename}: {e}")
            errors.append({"error": str(e), "file": file.filename})

    return UploadResponse(
        status="success",
        documents=results,
        total_uploaded=len(results),
        total_failed=len(errors),
        errors=errors,
    )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    query = select(Document).where(Document.deleted_at.is_(None))
    count_query = select(func.count()).select_from(Document).where(Document.deleted_at.is_(None))

    if status:
        query = query.where(Document.status == status)
        count_query = count_query.where(Document.status == status)

    total_result = await db.execute(count_query)
    total_count = total_result.scalar()

    query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in documents],
        total_count=total_count,
        skip=skip,
        limit=limit,
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.deleted_at.is_(None)
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(doc)


@router.post("/documents/{document_id}/summarize", response_model=SummaryResponse)
async def summarize_doc(
    document_id: str,
    request: SummarizeRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.deleted_at.is_(None)
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "ready":
        raise HTTPException(status_code=400, detail=f"Document is not ready (status: {doc.status})")

    try:
        summary_result = await summarize_document(
            document_id=document_id,
            level=request.summary_level,
            custom_prompt=request.custom_prompt,
            model=request.model,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

    token_log = TokenUsageLog(
        document_id=doc.id,
        operation="summarize",
        model=summary_result["model_used"],
        prompt_tokens=summary_result["tokens_used"]["prompt"],
        completion_tokens=summary_result["tokens_used"]["completion"],
        total_tokens=summary_result["tokens_used"]["total"],
        cost_usd=summary_result["estimated_cost_usd"],
    )
    db.add(token_log)
    await db.commit()

    return SummaryResponse(
        summary=summary_result["summary"],
        summary_level=summary_result["summary_level"],
        model_used=summary_result["model_used"],
        tokens_used=summary_result["tokens_used"],
        estimated_cost_usd=summary_result["estimated_cost_usd"],
        chunks_used=summary_result["chunks_used"],
        generation_time_ms=summary_result["generation_time_ms"],
    )


@router.post("/documents/{document_id}/query", response_model=QueryResponse)
async def query_document(
    document_id: str,
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.deleted_at.is_(None)
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "ready":
        raise HTTPException(status_code=400, detail=f"Document is not ready (status: {doc.status})")

    if not index_exists(document_id):
        raise HTTPException(status_code=404, detail="Document index not found")

    try:
        query_embeddings = await openrouter_service.embed([request.query])
        query_embedding = query_embeddings[0]
        chunks = search_index(document_id, query_embedding, top_k=request.top_k)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

    return QueryResponse(
        query=request.query,
        results=chunks,
        retrieved_at=datetime.utcnow(),
    )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.deleted_at.is_(None)
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.deleted_at = datetime.utcnow()
    await db.commit()

    delete_index(document_id)

    return {"status": "deleted", "document_id": document_id}
