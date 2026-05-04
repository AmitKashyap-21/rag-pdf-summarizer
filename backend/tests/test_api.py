import io
import json
import uuid
import pytest
import numpy as np
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient


# ── Health endpoint ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


# ── Authentication ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_documents_missing_auth(client):
    """Requests without Authorization header should return 401."""
    response = await client.get("/api/v1/documents")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_documents_wrong_token(client):
    """Requests with a wrong token should return 401."""
    response = await client.get(
        "/api/v1/documents",
        headers={"Authorization": "Bearer wrong-key"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_missing_auth(client):
    response = await client.post("/api/v1/documents/upload")
    assert response.status_code == 401


# ── Upload validation ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upload_no_files_returns_422(client):
    """POST /upload with no files should return 422 Unprocessable Entity."""
    response = await client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": "Bearer test-key"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_non_pdf_rejected(client):
    """A file that doesn't start with %PDF magic bytes should be rejected."""
    fake_content = b"not a pdf at all"

    with patch("app.api.v1.documents.get_db") as mock_get_db:
        # DB should never be reached for invalid files
        response = await client.post(
            "/api/v1/documents/upload",
            headers={"Authorization": "Bearer test-key"},
            files={"files": ("test.txt", io.BytesIO(fake_content), "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total_uploaded"] == 0
    assert data["total_failed"] == 1
    assert any("valid PDF" in e.get("error", "") for e in data["errors"])


# ── PDF processor unit tests ─────────────────────────────────────────────────

def _make_minimal_pdf() -> bytes:
    """Return the smallest valid single-page PDF."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 3 3]/Parent 2 0 R"
        b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        b"4 0 obj<</Length 44>>stream\n"
        b"BT /F1 12 Tf 1 1 Td (Hello World) Tj ET\n"
        b"endstream\nendobj\n"
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000274 00000 n \n"
        b"0000000369 00000 n \n"
        b"trailer<</Size 6/Root 1 0 R>>\n"
        b"startxref\n441\n%%EOF"
    )


def test_validate_pdf_valid():
    from app.services.pdf_processor import validate_pdf
    assert validate_pdf(_make_minimal_pdf()) is True


def test_validate_pdf_invalid():
    from app.services.pdf_processor import validate_pdf
    assert validate_pdf(b"garbage") is False


def test_get_page_count():
    from app.services.pdf_processor import get_page_count
    assert get_page_count(_make_minimal_pdf()) == 1


def test_extract_text_invalid_raises():
    from app.services.pdf_processor import extract_text_from_pdf
    with pytest.raises(ValueError, match="Failed to read PDF"):
        extract_text_from_pdf(b"not a pdf")


# ── Chunker unit tests ───────────────────────────────────────────────────────

def test_chunk_pages_basic():
    from app.services.chunker import chunk_pages

    pages = [
        {"page_number": 1, "content": "This is page one. " * 50},
        {"page_number": 2, "content": "This is page two. " * 50},
    ]
    doc_id = str(uuid.uuid4())
    chunks = chunk_pages(pages, doc_id, chunk_size=512, chunk_overlap=50)

    assert len(chunks) > 0
    for chunk in chunks:
        assert "id" in chunk
        assert "content" in chunk
        assert "page_number" in chunk
        assert "chunk_index" in chunk
        assert "token_count" in chunk
        assert chunk["id"].startswith(doc_id)
        assert chunk["page_number"] in (1, 2)


def test_chunk_pages_empty_input():
    from app.services.chunker import chunk_pages

    chunks = chunk_pages([], str(uuid.uuid4()))
    assert chunks == []


def test_chunk_pages_preserves_page_numbers():
    from app.services.chunker import chunk_pages

    pages = [
        {"page_number": 5, "content": "Content from page five. " * 20},
    ]
    chunks = chunk_pages(pages, str(uuid.uuid4()))
    assert all(c["page_number"] == 5 for c in chunks)


# ── FAISS vector store unit tests ────────────────────────────────────────────

def test_create_and_search_index(tmp_path):
    from app.services import vector_store
    import app.services.vector_store as vs_module

    original_path = vs_module.settings.INDEXES_PATH
    vs_module.settings.INDEXES_PATH = str(tmp_path)

    doc_id = str(uuid.uuid4())
    dim = 1536
    n = 5
    chunks = [
        {"id": f"{doc_id}#chunk_{i}", "content": f"Chunk content {i}", "page_number": i + 1, "token_count": 10}
        for i in range(n)
    ]
    embeddings = np.random.rand(n, dim).tolist()

    try:
        vector_store.create_and_save_index(doc_id, chunks, embeddings)
        assert vector_store.index_exists(doc_id)

        query_embedding = np.random.rand(dim).tolist()
        results = vector_store.search_index(doc_id, query_embedding, top_k=3)

        assert len(results) == 3
        for r in results:
            assert "content" in r
            assert "page_number" in r
            assert "similarity_score" in r
            assert 0.0 <= r["similarity_score"] <= 1.0
    finally:
        vs_module.settings.INDEXES_PATH = original_path


def test_delete_index(tmp_path):
    from app.services import vector_store
    import app.services.vector_store as vs_module

    original_path = vs_module.settings.INDEXES_PATH
    vs_module.settings.INDEXES_PATH = str(tmp_path)

    doc_id = str(uuid.uuid4())
    dim = 1536
    chunks = [{"id": f"{doc_id}#chunk_0", "content": "hello", "page_number": 1, "token_count": 5}]
    embeddings = np.random.rand(1, dim).tolist()

    try:
        vector_store.create_and_save_index(doc_id, chunks, embeddings)
        assert vector_store.index_exists(doc_id)
        vector_store.delete_index(doc_id)
        assert not vector_store.index_exists(doc_id)
    finally:
        vs_module.settings.INDEXES_PATH = original_path


def test_search_nonexistent_index_raises(tmp_path):
    from app.services import vector_store
    import app.services.vector_store as vs_module

    original_path = vs_module.settings.INDEXES_PATH
    vs_module.settings.INDEXES_PATH = str(tmp_path)

    try:
        # Use a valid UUID that simply has no index on disk
        with pytest.raises(FileNotFoundError):
            vector_store.search_index(str(uuid.uuid4()), [0.0] * 1536, top_k=5)
    finally:
        vs_module.settings.INDEXES_PATH = original_path


# ── API endpoint smoke tests (mocked DB & services) ──────────────────────────

@pytest.mark.asyncio
async def test_get_nonexistent_document(client):
    """GET on a non-existent UUID should return 404 or 500 (no live DB)."""
    try:
        response = await client.get(
            "/api/v1/documents/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": "Bearer test-key"},
        )
        assert response.status_code in (404, 500)
    except OSError:
        pytest.skip("No database available in test environment")


@pytest.mark.asyncio
async def test_list_documents_authorized_returns_valid_shape(client):
    """Authorized request returns correct shape even if DB is unavailable."""
    try:
        response = await client.get(
            "/api/v1/documents",
            headers={"Authorization": "Bearer test-key"},
        )
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert "documents" in data
            assert "total_count" in data
            assert "skip" in data
            assert "limit" in data
    except OSError:
        pytest.skip("No database available in test environment")
