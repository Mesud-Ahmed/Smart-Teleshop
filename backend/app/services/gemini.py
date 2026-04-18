import base64

import httpx

from app.config import Settings
from app.models import ProductDescription


class GeminiService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def describe_product(self, image_bytes: bytes, mime_type: str) -> ProductDescription:
        if not self.settings.gemini_api_key:
            return self._fallback_description()

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "You are naming inventory for a Telegram mini shop. "
                                "Identify the product as specifically as possible from the photo. "
                                "Return JSON with four keys: "
                                "`name` as a concise seller-friendly title, "
                                "`category` as a practical retail category, "
                                "`fingerprint_text` as one sentence describing visually distinctive traits "
                                "like color, material, shape, pattern, packaging, and likely product type, "
                                "and `confidence_note` as one short sentence about certainty."
                            )
                        },
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64.b64encode(image_bytes).decode("utf-8"),
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "category": {"type": "string"},
                        "fingerprint_text": {"type": "string"},
                        "confidence_note": {"type": "string"},
                    },
                    "required": ["name", "category", "fingerprint_text", "confidence_note"],
                },
            },
        }
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.settings.gemini_model}:generateContent?key={self.settings.gemini_api_key}"
        )

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text")
        )
        if not text:
            return self._fallback_description()

        return ProductDescription.model_validate_json(text)

    def _fallback_description(self) -> ProductDescription:
        return ProductDescription(
            name="Catalog Item",
            category="General Merchandise",
            fingerprint_text="Generic product image with limited identification because Gemini is not configured.",
            confidence_note="Fallback label used because Gemini is not configured.",
        )
