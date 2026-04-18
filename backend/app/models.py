from typing import List, Optional

from pydantic import BaseModel, Field


class ProductRecord(BaseModel):
    id: str
    name: str
    category: str
    cost_price: float = Field(ge=0)
    sale_price: float = Field(ge=0)
    stock_qty: int = Field(ge=0)
    image_url: Optional[str] = None
    fingerprint_text: Optional[str] = None
    embedding_vector: List[float]


class ProductCreate(BaseModel):
    name: str
    category: str
    cost_price: float = Field(ge=0)
    sale_price: float = Field(ge=0)
    stock_qty: int = Field(ge=0)
    image_url: Optional[str] = None
    fingerprint_text: Optional[str] = None
    embedding_vector: List[float]


class ProductMatchResult(BaseModel):
    id: str
    name: str
    category: str
    sale_price: float
    stock_qty: int
    image_url: Optional[str] = None
    similarity: float


class SaleCreate(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1)
    sale_price: float = Field(ge=0)
    cost_price: float = Field(ge=0)


class SaleRecord(BaseModel):
    product_id: str
    quantity: int
    sale_price: float
    cost_price: float
    profit: float


class ProductDescription(BaseModel):
    name: str
    category: str
    fingerprint_text: str
    confidence_note: str


class StockAlert(BaseModel):
    id: str
    name: str
    stock_qty: int
    severity: str


class DashboardSummary(BaseModel):
    total_daily_profit: float
    total_sales_today: int
    total_products: int
    low_stock_count: int
    stock_alerts: List[StockAlert]
