import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from supabase import Client, create_client

from app.config import Settings
from app.models import DashboardSummary, ProductCreate, SaleRecord, StockAlert


LOCAL_PRODUCTS: List[Dict[str, Any]] = []
LOCAL_SALES: List[Dict[str, Any]] = []


class InventoryRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client: Optional[Client] = None
        if settings.supabase_url and settings.supabase_key:
            self.client = create_client(settings.supabase_url, settings.supabase_key)

    async def is_ready(self) -> bool:
        if not self.client:
            return False
        try:
            self.client.table(self.settings.supabase_products_table).select("id").limit(1).execute()
            return True
        except Exception:
            return False

    async def create_product(self, product: ProductCreate) -> Dict[str, Any]:
        payload = product.model_dump()
        if not self.client:
            payload["id"] = str(uuid4())
            payload["created_at"] = datetime.now(timezone.utc).isoformat()
            LOCAL_PRODUCTS.append(payload)
            return payload

        response = self.client.table(self.settings.supabase_products_table).insert(payload).execute()
        return response.data[0]

    async def match_products(self, embedding_vector: List[float], limit: int = 3) -> List[Dict[str, Any]]:
        if not self.client:
            scored_matches = []
            for product in LOCAL_PRODUCTS:
                similarity = self._cosine_similarity(
                    embedding_vector,
                    product["embedding_vector"],
                )
                scored_matches.append(
                    {
                        "id": product["id"],
                        "name": product["name"],
                        "category": product["category"],
                        "sale_price": product["sale_price"],
                        "stock_qty": product["stock_qty"],
                        "image_url": product.get("image_url"),
                        "similarity": similarity,
                    }
                )
            return sorted(scored_matches, key=lambda item: item["similarity"], reverse=True)[:limit]

        response = self.client.rpc(
            "match_products",
            {"query_embedding": embedding_vector, "match_count": limit},
        ).execute()
        return response.data or []

    async def fetch_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            for product in LOCAL_PRODUCTS:
                if product["id"] == product_id:
                    return product
            return None

        response = (
            self.client.table(self.settings.supabase_products_table)
            .select("*")
            .eq("id", product_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    async def decrement_stock(self, product_id: str, quantity: int) -> None:
        if not self.client:
            for product in LOCAL_PRODUCTS:
                if product["id"] == product_id:
                    product["stock_qty"] = max(int(product["stock_qty"]) - quantity, 0)
            return

        product = await self.fetch_product(product_id)
        if not product:
            return

        new_stock = max(int(product["stock_qty"]) - quantity, 0)
        (
            self.client.table(self.settings.supabase_products_table)
            .update({"stock_qty": new_stock})
            .eq("id", product_id)
            .execute()
        )

    async def create_sale(self, sale: SaleRecord) -> Dict[str, Any]:
        payload = sale.model_dump()
        if not self.client:
            payload["id"] = str(uuid4())
            payload["created_at"] = datetime.now(timezone.utc).isoformat()
            LOCAL_SALES.append(payload)
            return payload

        response = self.client.table(self.settings.supabase_sales_table).insert(payload).execute()
        return response.data[0]

    async def get_dashboard_summary(self) -> DashboardSummary:
        if not self.client:
            today = datetime.now(timezone.utc).date()
            sales_today = [
                sale
                for sale in LOCAL_SALES
                if datetime.fromisoformat(sale["created_at"]).date() == today
            ]
            alerts = self._build_stock_alerts(LOCAL_PRODUCTS)
            return DashboardSummary(
                total_daily_profit=round(sum(float(sale["profit"]) for sale in sales_today), 2),
                total_sales_today=len(sales_today),
                total_products=len(LOCAL_PRODUCTS),
                low_stock_count=len(alerts),
                stock_alerts=alerts,
            )

        sales_response = self.client.table(self.settings.supabase_sales_table).select(
            "profit,created_at"
        ).execute()
        products_response = self.client.table(self.settings.supabase_products_table).select(
            "id,name,stock_qty"
        ).execute()

        sales_rows = sales_response.data or []
        product_rows = products_response.data or []
        today = datetime.now(timezone.utc).date()
        sales_today = [
            sale
            for sale in sales_rows
            if datetime.fromisoformat(sale["created_at"].replace("Z", "+00:00")).date() == today
        ]
        alerts = self._build_stock_alerts(product_rows)
        return DashboardSummary(
            total_daily_profit=round(sum(float(sale["profit"]) for sale in sales_today), 2),
            total_sales_today=len(sales_today),
            total_products=len(product_rows),
            low_stock_count=len(alerts),
            stock_alerts=alerts,
        )

    def _build_stock_alerts(self, products: List[Dict[str, Any]]) -> List[StockAlert]:
        alerts: List[StockAlert] = []
        for product in products:
            quantity = int(product["stock_qty"])
            if quantity == 0:
                severity = "red"
            elif quantity < 3:
                severity = "yellow"
            else:
                continue
            alerts.append(
                StockAlert(
                    id=str(product["id"]),
                    name=product["name"],
                    stock_qty=quantity,
                    severity=severity,
                )
            )
        return alerts

    def _cosine_similarity(self, left: List[float], right: List[float]) -> float:
        dot = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)
