"""Dashboard schemas for API responses."""
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class DashboardSummary(BaseModel):
    """Dashboard summary statistics."""
    
    total_products: int = Field(..., description="จำนวนสินค้าทั้งหมดในคลัง")
    total_quantity: int = Field(..., description="จำนวนสินค้ารวมทั้งหมด")
    low_stock_count: int = Field(..., description="จำนวนสินค้าที่ quantity < reorder_point")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_products": 25,
                "total_quantity": 450,
                "low_stock_count": 3
            }
        }


class RecentTransaction(BaseModel):
    """Recent transaction with items summary."""
    
    transaction_id: str = Field(..., description="Transaction ID")
    receipt_id: str = Field(..., description="Receipt ID")
    created_at: datetime = Field(..., description="วันที่-เวลาที่สร้าง transaction")
    total_items: int = Field(..., description="จำนวนรายการสินค้าทั้งหมด")
    items_summary: List[str] = Field(..., description="สรุปรายการสินค้า")
    
    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
                "receipt_id": "660e8400-e29b-41d4-a716-446655440000",
                "created_at": "2025-10-20T10:30:00Z",
                "total_items": 3,
                "items_summary": [
                    "โค้ก 325 มล. (6 กระป๋อง)",
                    "น้ำเปล่า (12 ขวด)",
                    "ขนมปัง (2 ถุง)"
                ]
            }
        }


class LowStockProduct(BaseModel):
    """Product with low stock alert."""
    
    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="ชื่อสินค้า")
    quantity: int = Field(..., description="จำนวนปัจจุบัน")
    unit: str = Field(..., description="หน่วยนับ")
    reorder_point: int = Field(..., description="จุดสั่งซื้อ")
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "770e8400-e29b-41d4-a716-446655440000",
                "product_name": "โค้ก 325 มล.",
                "quantity": 5,
                "unit": "กระป๋อง",
                "reorder_point": 10
            }
        }


class StockTrendData(BaseModel):
    """Stock trend data for a specific date."""
    
    date: str = Field(..., description="วันที่ (YYYY-MM-DD)")
    total_items_added: int = Field(..., description="จำนวนสินค้าที่เพิ่มในวันนั้น")
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-10-20",
                "total_items_added": 45
            }
        }
