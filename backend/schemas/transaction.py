"""Pydantic schemas for transactions."""
from pydantic import BaseModel, Field, field_validator
from typing import List
from datetime import datetime


class TransactionItemCreate(BaseModel):
    """Schema for creating a transaction item."""
    product_id: str = Field(..., min_length=1)
    product_name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., gt=0, description="จำนวนสินค้า (ต้องมากกว่า 0)")
    unit: str = Field(..., min_length=1, max_length=50)
    original_text: str = Field(..., min_length=1, max_length=1000, description="ข้อความต้นฉบับจากใบเสร็จ")
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Validate that quantity is positive"""
        if v <= 0:
            raise ValueError('จำนวนสินค้าต้องมากกว่า 0')
        return v
    
    @field_validator('product_id', 'product_name', 'unit', 'original_text')
    @classmethod
    def not_empty(cls, v: str) -> str:
        """Validate that string fields are not empty"""
        if not v or not v.strip():
            raise ValueError('ข้อมูลต้องไม่เป็นค่าว่าง')
        return v.strip()


class TransactionItemResponse(BaseModel):
    """Schema for transaction item response."""
    id: str
    transaction_id: str
    product_id: str
    product_name: str
    quantity: int
    unit: str
    original_text: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class TransactionCreate(BaseModel):
    """Schema for creating a transaction."""
    receipt_id: str = Field(..., min_length=1)
    items: List[TransactionItemCreate] = Field(..., min_length=1, description="รายการสินค้าอย่างน้อย 1 รายการ")
    
    @field_validator('receipt_id')
    @classmethod
    def receipt_id_not_empty(cls, v: str) -> str:
        """Validate that receipt_id is not empty"""
        if not v or not v.strip():
            raise ValueError('receipt_id ต้องไม่เป็นค่าว่าง')
        return v.strip()
    
    @field_validator('items')
    @classmethod
    def items_not_empty(cls, v: List[TransactionItemCreate]) -> List[TransactionItemCreate]:
        """Validate that items list is not empty"""
        if not v or len(v) == 0:
            raise ValueError('ต้องมีรายการสินค้าอย่างน้อย 1 รายการ')
        return v


class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    id: str
    receipt_id: str
    total_items: int
    created_at: datetime
    items: List[TransactionItemResponse]
    
    class Config:
        from_attributes = True
