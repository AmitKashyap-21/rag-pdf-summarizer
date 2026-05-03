# DocuRAG – RAG-Based PDF Summarization & Query System

A production-hardened RAG application for intelligent PDF document summarization and semantic querying.

## Tech Stack
- **Backend**: FastAPI + Python 3.11
- **LLM/Embeddings**: OpenRouter (GPT-3.5-Turbo + text-embedding-3-small)
- **Vector Store**: FAISS (local disk-based)
- **Database**: PostgreSQL
- **Frontend**: React + Tailwind CSS + Vite

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenRouter API key (https://openrouter.ai)

### Setup
1. Clone the repository
2. Copy `.env.example` to `.env`
3. Set `OPENROUTER_API_KEY` in `.env`
4. Run: `docker-compose up`

### Local Development (without Docker)

#### Backend
```bash
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env
# Edit .env with your values
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

### API Docs
Visit http://localhost:8000/docs for interactive Swagger UI documentation.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/documents/upload | Upload one or more PDF files |
| GET | /api/v1/documents | List all documents |
| GET | /api/v1/documents/{id} | Get document details |
| POST | /api/v1/documents/{id}/summarize | Generate AI summary |
| POST | /api/v1/documents/{id}/query | Semantic search query |
| DELETE | /api/v1/documents/{id} | Delete document |
| GET | /health | Health check |

## Authentication
All API endpoints require Bearer token authentication:
```
Authorization: Bearer {API_KEY}
```
Set `API_KEY` in your `.env` file (default: `changeme`).

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| OPENROUTER_API_KEY | OpenRouter API key | Required |
| OPENROUTER_LLM_MODEL | LLM model | openai/gpt-3.5-turbo |
| OPENROUTER_EMBEDDING_MODEL | Embedding model | openai/text-embedding-3-small |
| DATABASE_URL | PostgreSQL connection URL | See .env.example |
| API_KEY | Bearer token for API auth | changeme |
| MAX_FILE_SIZE_MB | Maximum PDF file size | 50 |
| CHUNK_SIZE | Token size per chunk | 512 |
