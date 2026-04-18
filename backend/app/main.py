from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.models import (
    DashboardSummary,
    ProductCreate,
    ProductMatchResult,
    ProductRecord,
    SaleCreate,
    SaleRecord,
)
from app.services.embeddings import EmbeddingService
from app.services.gemini import GeminiService
from app.services.repository import InventoryRepository
from app.services.storage import ImageStorageService


def build_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def healthcheck(
        app_settings: Settings = Depends(get_settings),
    ) -> dict[str, str | bool]:
        repo = InventoryRepository(app_settings)
        supabase_ready = await repo.is_ready() if repo.client else False
        return {
            "status": "ok",
            "environment": app_settings.app_env,
            "supabase_configured": bool(app_settings.supabase_url and app_settings.supabase_key),
            "supabase_ready": supabase_ready,
            "gemini_configured": bool(app_settings.gemini_api_key),
        }

    @app.post(f"{settings.api_prefix}/products/onboard")
    async def onboard_product(
        cost_price: float = Form(...),
        sale_price: float = Form(...),
        stock_qty: int = Form(...),
        image: UploadFile = File(...),
        app_settings: Settings = Depends(get_settings),
    ) -> dict:
        image_bytes = await image.read()
        gemini = GeminiService(app_settings)
        embeddings = EmbeddingService(app_settings)
        repo = InventoryRepository(app_settings)
        storage = ImageStorageService(app_settings, repo)

        description = await gemini.describe_product(
            image_bytes=image_bytes,
            mime_type=image.content_type or "image/jpeg",
        )
        fingerprint_for_embedding = " | ".join(
            [description.name, description.category, description.fingerprint_text]
        )
        embedding_vector = await embeddings.embed_text(fingerprint_for_embedding)
        image_url = await storage.store_product_image(
            image_bytes=image_bytes,
            mime_type=image.content_type or "image/jpeg",
        )

        product = ProductCreate(
            name=description.name,
            category=description.category,
            cost_price=cost_price,
            sale_price=sale_price,
            stock_qty=stock_qty,
            image_url=image_url,
            fingerprint_text=description.fingerprint_text,
            embedding_vector=embedding_vector,
        )
        saved = await repo.create_product(product)
        return {
            "message": "Product saved",
            "product": saved,
            "ai_description": description.model_dump(),
        }

    @app.post(f"{settings.api_prefix}/products/match", response_model=list[ProductMatchResult])
    async def match_product(
        image: UploadFile = File(...),
        app_settings: Settings = Depends(get_settings),
    ) -> list[ProductMatchResult]:
        image_bytes = await image.read()
        gemini = GeminiService(app_settings)
        embeddings = EmbeddingService(app_settings)
        repo = InventoryRepository(app_settings)

        description = await gemini.describe_product(
            image_bytes=image_bytes,
            mime_type=image.content_type or "image/jpeg",
        )
        fingerprint_for_embedding = " | ".join(
            [description.name, description.category, description.fingerprint_text]
        )
        vector = await embeddings.embed_text(fingerprint_for_embedding)
        matches = await repo.match_products(vector, limit=3)
        return [ProductMatchResult(**item) for item in matches]

    @app.get(f"{settings.api_prefix}/products/{{product_id}}", response_model=ProductRecord)
    async def get_product(
        product_id: str,
        app_settings: Settings = Depends(get_settings),
    ) -> ProductRecord:
        repo = InventoryRepository(app_settings)
        product = await repo.fetch_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return ProductRecord(**product)

    @app.post(f"{settings.api_prefix}/sales")
    async def create_sale(
        payload: SaleCreate,
        app_settings: Settings = Depends(get_settings),
    ) -> dict:
        repo = InventoryRepository(app_settings)
        product = await repo.fetch_product(payload.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if int(product["stock_qty"]) < payload.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")

        record = SaleRecord(
            product_id=payload.product_id,
            quantity=payload.quantity,
            sale_price=payload.sale_price,
            cost_price=payload.cost_price,
            profit=(payload.sale_price - payload.cost_price) * payload.quantity,
        )
        saved = await repo.create_sale(record)
        await repo.decrement_stock(payload.product_id, payload.quantity)
        return {"message": "Sale logged", "sale": saved}

    @app.get(f"{settings.api_prefix}/dashboard/summary", response_model=DashboardSummary)
    async def dashboard_summary(
        app_settings: Settings = Depends(get_settings),
    ) -> DashboardSummary:
        repo = InventoryRepository(app_settings)
        return await repo.get_dashboard_summary()

    return app


app = build_app()
