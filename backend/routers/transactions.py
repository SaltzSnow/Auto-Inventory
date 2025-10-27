"""Transaction router for managing transaction history."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, date
from slowapi import Limiter
from slowapi.util import get_remote_address
from database import get_db
from models.transaction import Transaction, TransactionItem
from models.receipt import Receipt
from schemas.transaction import TransactionResponse, TransactionItemResponse
import logging

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(
    prefix="/api/transactions",
    tags=["transactions"]
)


@router.get("", response_model=List[TransactionResponse])
@limiter.limit("100/minute")
async def get_transactions(
    request: Request,
    skip: int = Query(0, ge=0, description="จำนวนรายการที่จะข้าม"),
    limit: int = Query(20, ge=1, le=100, description="จำนวนรายการสูงสุดที่จะดึง"),
    db: AsyncSession = Depends(get_db)
):
    """
    ดึงรายการ transactions ทั้งหมดพร้อม pagination.
    Uses eager loading with selectinload() for better performance.
    
    เรียงตาม created_at DESC (ล่าสุดก่อน)
    """
    try:
        # Query transactions with pagination and eager loading of items
        result = await db.execute(
            select(Transaction)
            .options(selectinload(Transaction.items))
            .order_by(Transaction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        transactions = result.scalars().all()
        
        # Build response with items for each transaction
        response = []
        for transaction in transactions:
            # Items are already loaded via selectinload
            items = transaction.items
            
            response.append(
                TransactionResponse(
                    id=transaction.id,
                    receipt_id=transaction.receipt_id,
                    total_items=transaction.total_items,
                    created_at=transaction.created_at,
                    items=[
                        TransactionItemResponse(
                            id=item.id,
                            transaction_id=item.transaction_id,
                            product_id=item.product_id,
                            product_name=item.product_name,
                            quantity=item.quantity,
                            unit=item.unit,
                            original_text=item.original_text,
                            created_at=item.created_at
                        )
                        for item in items
                    ]
                )
            )
        
        logger.info(f"Retrieved {len(response)} transactions (skip={skip}, limit={limit})")
        return response
        
    except Exception as e:
        logger.error(f"Error retrieving transactions: {str(e)}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงข้อมูล transactions")


@router.get("/{transaction_id}", response_model=TransactionResponse)
@limiter.limit("100/minute")
async def get_transaction_detail(
    request: Request,
    transaction_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    ดึงรายละเอียดเต็มของ transaction รวมถึง items และ receipt image URL.
    Uses eager loading with selectinload() for better performance.
    """
    try:
        # Get transaction with eager loading of items
        result = await db.execute(
            select(Transaction)
            .options(selectinload(Transaction.items))
            .where(Transaction.id == transaction_id)
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise HTTPException(status_code=404, detail=f"ไม่พบ transaction ที่มี id {transaction_id}")
        
        # Items are already loaded via selectinload
        items = transaction.items
        
        # Build response
        response = TransactionResponse(
            id=transaction.id,
            receipt_id=transaction.receipt_id,
            total_items=transaction.total_items,
            created_at=transaction.created_at,
            items=[
                TransactionItemResponse(
                    id=item.id,
                    transaction_id=item.transaction_id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit=item.unit,
                    original_text=item.original_text,
                    created_at=item.created_at
                )
                for item in items
            ]
        )
        
        logger.info(f"Retrieved transaction {transaction_id} with {len(items)} items")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving transaction {transaction_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการดึงข้อมูล transaction")


@router.get("/search", response_model=List[TransactionResponse])
@limiter.limit("100/minute")
async def search_transactions(
    request: Request,
    q: Optional[str] = Query(None, description="ค้นหาตามชื่อสินค้า"),
    start_date: Optional[date] = Query(None, description="วันที่เริ่มต้น (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="วันที่สิ้นสุด (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0, description="จำนวนรายการที่จะข้าม"),
    limit: int = Query(20, ge=1, le=100, description="จำนวนรายการสูงสุดที่จะดึง"),
    db: AsyncSession = Depends(get_db)
):
    """
    ค้นหา transactions โดย filter ตามชื่อสินค้าหรือช่วงวันที่.
    
    - q: ค้นหาตามชื่อสินค้าใน transaction items (case-insensitive)
    - start_date: กรองตั้งแต่วันที่นี้เป็นต้นไป
    - end_date: กรองจนถึงวันที่นี้
    """
    try:
        # Build base query with eager loading
        query = select(Transaction).options(selectinload(Transaction.items)).distinct()
        
        # Apply filters
        conditions = []
        
        # Date range filter
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            conditions.append(Transaction.created_at >= start_datetime)
        
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            conditions.append(Transaction.created_at <= end_datetime)
        
        # Product name filter - need to join with transaction_items
        if q:
            # Subquery to find transaction IDs that have matching product names
            subquery = select(TransactionItem.transaction_id).where(
                TransactionItem.product_name.ilike(f"%{q}%")
            )
            conditions.append(Transaction.id.in_(subquery))
        
        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))
        
        # Order and paginate
        query = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        # Build response with items for each transaction
        response = []
        for transaction in transactions:
            # Items are already loaded via selectinload
            items = transaction.items
            
            response.append(
                TransactionResponse(
                    id=transaction.id,
                    receipt_id=transaction.receipt_id,
                    total_items=transaction.total_items,
                    created_at=transaction.created_at,
                    items=[
                        TransactionItemResponse(
                            id=item.id,
                            transaction_id=item.transaction_id,
                            product_id=item.product_id,
                            product_name=item.product_name,
                            quantity=item.quantity,
                            unit=item.unit,
                            original_text=item.original_text,
                            created_at=item.created_at
                        )
                        for item in items
                    ]
                )
            )
        
        logger.info(
            f"Search returned {len(response)} transactions "
            f"(q={q}, start_date={start_date}, end_date={end_date})"
        )
        return response
        
    except Exception as e:
        logger.error(f"Error searching transactions: {str(e)}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการค้นหา transactions")
