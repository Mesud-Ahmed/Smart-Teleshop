import hashlib
from typing import List

import httpx

from app.config import Settings


class EmbeddingService:
    def __init__(self, settings: Settings, dimension: int = 768) -> None:
        self.settings = settings
        self.dimension = dimension

    async def embed_text(self, text: str) -> List[float]:
        if self.settings.gemini_api_key:
            payload = {
                "content": {"parts": [{"text": text}]},
                "output_dimensionality": self.dimension,
            }
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self.settings.embedding_model}:embedContent"
            )
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url,
                    headers={"x-goog-api-key": self.settings.gemini_api_key},
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
            embedding = data.get("embedding", {}).get("values")
            if embedding:
                return embedding

        # Deterministic fallback so the app can still be exercised without external services.
        digest = hashlib.sha512(text.encode("utf-8")).digest()
        seed = list(digest) * ((self.dimension // len(digest)) + 1)
        vector = [((value / 255.0) * 2.0) - 1.0 for value in seed[: self.dimension]]
        return vector
