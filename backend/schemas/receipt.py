"""Pydantic schemas for receipt processing."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ExtractedItem(BaseModel):
    """Item extracted from receipt by AI."""
    name: str = Field(..., min_length=1, max_length=500, description="ชื่อสินค้าที่สกัดได้")
    quantity: str = Field(..., min_length=1, max_length=100, description="จำนวนและหน่วย (เช่น '6 กระป๋อง', '12 ขวด')")
    original_text: str = Field(..., min_length=1, max_length=1000, description="ข้อความต้นฉบับจากใบเสร็จ")
    
    @field_validator('name', 'quantity', 'original_text')
    @classmethod
    def not_empty(cls, v: str) -> str:
        """Validate that fields are not empty or whitespace only"""
        if not v or not v.strip():
            raise ValueError('ข้อมูลต้องไม่เป็นค่าว่าง')
        return v.strip()


class MatchedProduct(BaseModel):
    """Product matched from inventory."""
    product_id: str = Field(..., min_length=1)
    product_name: str = Field(..., min_length=1, max_length=255)
    unit: str = Field(..., min_length=1, max_length=50)
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="คะแนนความคล้าย (0-1)")
    
    @field_validator('similarity_score')
    @classmethod
    def validate_similarity(cls, v: float) -> float:
        """Validate that similarity score is between 0 and 1"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('คะแนนความคล้ายต้องอยู่ระหว่าง 0 ถึง 1')
        return v


class ValidatedItem(BaseModel):
    """Validated and converted item ready for inventory update."""
    product_id: str = Field(..., min_length=1)
    product_name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., gt=0, description="จำนวนสินค้า (ต้องมากกว่า 0)")
    unit: str = Field(..., min_length=1, max_length=50)
    confidence: float = Field(..., ge=0.0, le=1.0, description="ความมั่นใจ (0-1)")
    original_text: str = Field(..., min_length=1, max_length=1000)
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Validate that quantity is positive"""
        if v <= 0:
            raise ValueError('จำนวนสินค้าต้องมากกว่า 0')
        return v
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate that confidence is between 0 and 1"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('ความมั่นใจต้องอยู่ระหว่าง 0 ถึง 1')
        return v
