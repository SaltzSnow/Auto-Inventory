"""Product schemas for request/response validation."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


# Allowed units for products
ALLOWED_UNITS = [
    "ชิ้น", "กระป๋อง", "ขวด", "แพ็ค", "กล่อง", "ถุง", 
    "ห่อ", "ลัง", "โหล", "กิโลกรัม", "กรัม", "ลิตร", 
    "มิลลิลิตร", "เมตร", "เซนติเมตร", "อัน", "แผ่น"
]


class ProductCreate(BaseModel):
    """Schema for creating a new product."""
    name: str = Field(..., min_length=1, max_length=255, description="ชื่อสินค้า")
    unit: str = Field(..., min_length=1, max_length=50, description="หน่วยนับ เช่น ชิ้น, กระป๋อง, ขวด")
    quantity: int = Field(default=0, ge=0, description="จำนวนสินค้าในคลัง")
    reorder_point: int = Field(default=0, ge=0, description="จุดสั่งซื้อ")
    description: Optional[str] = Field(None, max_length=1000, description="รายละเอียดเพิ่มเติม")
    force_without_embedding: bool = Field(default=False, description="บังคับสร้างสินค้าโดยไม่มี embedding (ฟีเจอร์ AI search จะไม่ทำงาน)")
    
    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Validate that name is not empty or whitespace only"""
        if not v or not v.strip():
            raise ValueError('ชื่อสินค้าต้องไม่เป็นค่าว่าง')
        return v.strip()
    
    @field_validator('unit')
    @classmethod
    def validate_unit(cls, v: str) -> str:
        """Validate that unit is not empty and is in allowed list"""
        if not v or not v.strip():
            raise ValueError('หน่วยนับต้องไม่เป็นค่าว่าง')
        
        v = v.strip()
        if v not in ALLOWED_UNITS:
            raise ValueError(
                f'หน่วยนับไม่ถูกต้อง กรุณาเลือกจาก: {", ".join(ALLOWED_UNITS)}'
            )
        return v
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Validate that quantity is non-negative"""
        if v < 0:
            raise ValueError('จำนวนสินค้าต้องไม่ติดลบ')
        return v
    
    @field_validator('reorder_point')
    @classmethod
    def validate_reorder_point(cls, v: int) -> int:
        """Validate that reorder_point is non-negative"""
        if v < 0:
            raise ValueError('จุดสั่งซื้อต้องไม่ติดลบ')
        return v


class ProductUpdate(BaseModel):
    """Schema for updating an existing product."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="ชื่อสินค้า")
    unit: Optional[str] = Field(None, min_length=1, max_length=50, description="หน่วยนับ")
    quantity: Optional[int] = Field(None, ge=0, description="จำนวนสินค้าในคลัง")
    reorder_point: Optional[int] = Field(None, ge=0, description="จุดสั่งซื้อ")
    description: Optional[str] = Field(None, max_length=1000, description="รายละเอียดเพิ่มเติม")
    
    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate that name is not empty or whitespace only"""
        if v is not None and (not v or not v.strip()):
            raise ValueError('ชื่อสินค้าต้องไม่เป็นค่าว่าง')
        return v.strip() if v else None
    
    @field_validator('unit')
    @classmethod
    def validate_unit(cls, v: Optional[str]) -> Optional[str]:
        """Validate that unit is not empty and is in allowed list"""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('หน่วยนับต้องไม่เป็นค่าว่าง')
            
            v = v.strip()
            if v not in ALLOWED_UNITS:
                raise ValueError(
                    f'หน่วยนับไม่ถูกต้อง กรุณาเลือกจาก: {", ".join(ALLOWED_UNITS)}'
                )
        return v
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: Optional[int]) -> Optional[int]:
        """Validate that quantity is non-negative"""
        if v is not None and v < 0:
            raise ValueError('จำนวนสินค้าต้องไม่ติดลบ')
        return v
    
    @field_validator('reorder_point')
    @classmethod
    def validate_reorder_point(cls, v: Optional[int]) -> Optional[int]:
        """Validate that reorder_point is non-negative"""
        if v is not None and v < 0:
            raise ValueError('จุดสั่งซื้อต้องไม่ติดลบ')
        return v


class ProductResponse(BaseModel):
    """Schema for product response."""
    id: str
    name: str
    unit: str
    quantity: int
    reorder_point: int
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }
