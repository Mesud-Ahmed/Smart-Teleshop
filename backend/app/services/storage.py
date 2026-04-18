from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.config import Settings
from app.services.repository import InventoryRepository


class ImageStorageService:
    def __init__(self, settings: Settings, repository: InventoryRepository) -> None:
        self.settings = settings
        self.repository = repository

    async def store_product_image(self, image_bytes: bytes, mime_type: str) -> str:
        if not self.repository.client:
            return build_data_url(image_bytes, mime_type)

        extension = guess_extension(mime_type)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        path = f"products/{timestamp}-{uuid4().hex}{extension}"
        self.repository.client.storage.from_(self.settings.supabase_storage_bucket).upload(
            path=path,
            file=image_bytes,
            file_options={
                "content-type": mime_type,
                "cache-control": "3600",
                "upsert": "false",
            },
        )
        return self.repository.client.storage.from_(self.settings.supabase_storage_bucket).get_public_url(
            path
        )


def guess_extension(mime_type: str) -> str:
    mapping = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/heic": ".heic",
    }
    return mapping.get(mime_type.lower(), Path("upload.bin").suffix or ".bin")


def build_data_url(image_bytes: bytes, mime_type: str) -> str:
    import base64

    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"
