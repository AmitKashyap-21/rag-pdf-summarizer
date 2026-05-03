import asyncio
import random
import logging
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

COST_PER_TOKEN = {
    "openai/gpt-3.5-turbo": {"prompt": 0.0000005, "completion": 0.0000015},
    "openai/gpt-4": {"prompt": 0.00003, "completion": 0.00006},
    "openai/text-embedding-3-small": {"prompt": 0.00000002, "completion": 0.0},
}

SUMMARY_CONFIGS = {
    "brief": {
        "max_tokens": 150,
        "system_prompt": "You are a concise summarizer. Provide 1-2 sentence summaries."
    },
    "medium": {
        "max_tokens": 500,
        "system_prompt": "You are a professional summarizer. Provide clear, well-structured summaries (2-3 paragraphs)."
    },
    "detailed": {
        "max_tokens": 2000,
        "system_prompt": "You are a thorough analyst. Provide comprehensive summaries with key details."
    }
}


class OpenRouterService:
    def __init__(self):
        self.base_url = settings.OPENROUTER_BASE_URL
        self.max_retries = settings.OPENROUTER_MAX_RETRIES
        self.timeout = settings.OPENROUTER_TIMEOUT

    @property
    def api_key(self) -> str:
        key = settings.OPENROUTER_API_KEY
        if not key:
            raise ValueError("OPENROUTER_API_KEY is not set")
        return key

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://rag-pdf-summarizer.app",
            "X-Title": "RAG PDF Summarizer"
        }

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts with retry."""
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/embeddings",
                        headers=self._headers(),
                        json={
                            "model": settings.OPENROUTER_EMBEDDING_MODEL,
                            "input": texts,
                            "encoding_format": "float"
                        }
                    )
                    if response.status_code == 429:
                        wait_time = (2 ** attempt) + random.uniform(0, 0.1 * attempt)
                        logger.warning(f"Rate limited on embeddings, waiting {wait_time:.1f}s")
                        await asyncio.sleep(wait_time)
                        continue
                    response.raise_for_status()
                    data = response.json()
                    embeddings = sorted(data["data"], key=lambda x: x["index"])
                    return [item["embedding"] for item in embeddings]
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ValueError("OpenRouter API key invalid")
                raise
        raise Exception("Max retries exceeded for embeddings")

    async def embed_in_batches(self, texts: List[str], batch_size: int = 50) -> List[List[float]]:
        """Embed texts in batches."""
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self.embed(batch)
            all_embeddings.extend(batch_embeddings)
        return all_embeddings

    async def summarize(
        self,
        context: str,
        level: str = "medium",
        custom_prompt: Optional[str] = None,
        model: str = None
    ) -> Dict[str, Any]:
        """Generate summary via LLM with retry."""
        if model is None:
            model = settings.OPENROUTER_LLM_MODEL

        config = SUMMARY_CONFIGS.get(level, SUMMARY_CONFIGS["medium"])
        system_prompt = config["system_prompt"]
        max_tokens = config["max_tokens"]

        if len(context) > 16000:
            context = context[:16000]
            logger.warning("Context truncated to 16000 characters")

        if custom_prompt:
            user_content = f"{custom_prompt}\n\nDocument content:\n{context}"
        else:
            user_content = f"Summarize the following document:\n\n{context}"

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self._headers(),
                        json={
                            "model": model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_content}
                            ],
                            "temperature": 0.7,
                            "max_tokens": max_tokens
                        }
                    )
                    if response.status_code == 429:
                        wait_time = (2 ** attempt) + random.uniform(0, 0.1 * attempt)
                        logger.warning(f"Rate limited on LLM, waiting {wait_time:.1f}s")
                        await asyncio.sleep(wait_time)
                        continue
                    if response.status_code == 401:
                        raise ValueError("OpenRouter API key invalid")
                    response.raise_for_status()

                    data = response.json()
                    usage = data.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", 0)

                    cost_rates = COST_PER_TOKEN.get(model, {"prompt": 0.0000005, "completion": 0.0000015})
                    cost_usd = (prompt_tokens * cost_rates["prompt"]) + (completion_tokens * cost_rates["completion"])

                    return {
                        "summary": data["choices"][0]["message"]["content"],
                        "model_used": model,
                        "tokens_used": {
                            "prompt": prompt_tokens,
                            "completion": completion_tokens,
                            "total": total_tokens
                        },
                        "estimated_cost_usd": cost_usd
                    }
            except httpx.TimeoutException:
                raise TimeoutError("LLM request timeout")
            except ValueError:
                raise
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.error(f"LLM attempt {attempt + 1} failed: {e}")

        raise Exception("Max retries exceeded for LLM")


openrouter_service = OpenRouterService()
