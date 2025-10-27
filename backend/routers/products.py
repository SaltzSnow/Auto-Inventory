"""Product API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from database import get_db
from schemas.product import ProductCreate, ProductUpdate, ProductResponse
from services.product_service import product_service
from exceptions import EmbeddingFailureError
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=List[ProductResponse])
@limiter.limit("100/minute")
async def get_products(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    ดึงรายการสินค้าทั้งหมด
    
    - **skip**: จำนวนรายการที่จะข้าม (สำหรับ pagination)
    - **limit**: จำนวนรายการสูงสุดที่จะส่งกลับ
    """
    try:
        products = await product_service.get_products(db, skip=skip, limit=limit)
        return products
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error getting products: {error_msg}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการดึงข้อมูลสินค้า\n\n{error_msg}")


@router.get("/search", response_model=List[ProductResponse])
@limiter.limit("100/minute")
async def search_products(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    ค้นหาสินค้าตามชื่อ (case-insensitive)
    
    - **q**: คำค้นหา
    - **skip**: จำนวนรายการที่จะข้าม
    - **limit**: จำนวนรายการสูงสุดที่จะส่งกลับ
    """
    try:
        products = await product_service.search_products(db, query=q, skip=skip, limit=limit)
        return products
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error searching products: {error_msg}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการค้นหาสินค้า\n\n{error_msg}")


@router.get("/{product_id}", response_model=ProductResponse)
@limiter.limit("100/minute")
async def get_product(
    request: Request,
    product_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    ดึงข้อมูลสินค้าตาม ID
    
    - **product_id**: ID ของสินค้า
    """
    try:
        product = await product_service.get_product_by_id(db, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="ไม่พบสินค้า")
        return product
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error getting product {product_id}: {error_msg}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการดึงข้อมูลสินค้า\n\n{error_msg}")


@router.post("", response_model=ProductResponse, status_code=201)
@limiter.limit("100/minute")
async def create_product(
    request: Request,
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    สร้างสินค้าใหม่
    
    ระบบจะสร้าง vector embedding จากชื่อสินค้าโดยอัตโนมัติ
    
    - **name**: ชื่อสินค้า (required)
    - **unit**: หน่วยนับ เช่น ชิ้น, กระป๋อง, ขวด (required)
    - **quantity**: จำนวนสินค้าในคลัง (default: 0)
    - **reorder_point**: จุดสั่งซื้อ (default: 0)
    - **description**: รายละเอียดเพิ่มเติม (optional)
    """
    try:
        product = await product_service.create_product(db, product_data)
        await db.commit()
        return product
    except EmbeddingFailureError as e:
        logger.warning(f"Embedding failure creating product: {e.message}")
        await db.rollback()
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details
            }
        )
    except ValueError as e:
        logger.warning(f"Validation error creating product: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error creating product: {error_msg}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการสร้างสินค้า\n\n{error_msg}")


@router.put("/{product_id}", response_model=ProductResponse)
@limiter.limit("100/minute")
async def update_product(
    request: Request,
    product_id: str,
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    แก้ไขข้อมูลสินค้า
    
    หากมีการเปลี่ยนชื่อสินค้า ระบบจะสร้าง vector embedding ใหม่โดยอัตโนมัติ
    
    - **name**: ชื่อสินค้า
    - **unit**: หน่วยนับ
    - **quantity**: จำนวนสินค้าในคลัง
    - **reorder_point**: จุดสั่งซื้อ
    - **description**: รายละเอียดเพิ่มเติม
    """
    try:
        product = await product_service.update_product(db, product_id, product_data)
        if not product:
            raise HTTPException(status_code=404, detail="ไม่พบสินค้า")
        await db.commit()
        return product
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error updating product: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error updating product {product_id}: {error_msg}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการแก้ไขสินค้า\n\n{error_msg}")


@router.delete("/{product_id}", status_code=204)
@limiter.limit("100/minute")
async def delete_product(
    request: Request,
    product_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    ลบสินค้า
    
    - **product_id**: ID ของสินค้าที่ต้องการลบ
    """
    try:
        deleted = await product_service.delete_product(db, product_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="ไม่พบสินค้า")
        await db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error deleting product {product_id}: {error_msg}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการลบสินค้า\n\n{error_msg}")
