from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    num_pages: int
    num_chunks: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        if hasattr(obj, 'id') and not isinstance(obj.id, str):
            data = {
                'id': str(obj.id),
                'filename': obj.filename,
                'file_size': obj.file_size,
                'num_pages': obj.num_pages,
                'num_chunks': obj.num_chunks,
                'status': obj.status,
                'created_at': obj.created_at,
                'updated_at': obj.updated_at,
            }
            return cls(**data)
        return super().model_validate(obj, **kwargs)


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total_count: int
    skip: int
    limit: int


class UploadResponse(BaseModel):
    status: str
    documents: List[DocumentResponse]
    total_uploaded: int
    total_failed: int
    errors: List[Dict[str, Any]]


class SummarizeRequest(BaseModel):
    summary_level: Literal["brief", "medium", "detailed"] = "medium"
    custom_prompt: Optional[str] = None
    model: str = "openai/gpt-3.5-turbo"


class SummaryResponse(BaseModel):
    summary: str
    summary_level: str
    model_used: str
    tokens_used: Dict[str, int]
    estimated_cost_usd: float
    chunks_used: List[Dict[str, Any]]
    generation_time_ms: int


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class QueryResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    retrieved_at: datetime
