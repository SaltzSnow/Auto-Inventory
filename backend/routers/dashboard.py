"""Dashboard router for summary statistics and insights."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List
from datetime import datetime, timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address
from database import get_db
from models.product import Product
from models.transaction import Transaction, TransactionItem
from schemas.dashboard import (
    DashboardSummary,
    RecentTransaction,
    LowStockProduct,
    StockTrendData
)
import logging

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(
    prefix="/api/dashboard",
    tags=["dashboard"]
)


@router.get("/summary", response_model=DashboardSummary)
@limiter.limit("100/minute")
@cache(expire=300)  # Cache for 5 minutes
async def get_dashboard_summary(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Get dashboard summary statistics.
    Cached for 5 minutes to improve performance.
    
    Returns:
        - total_products: จำนวนสินค้าทั้งหมดในคลัง
        - total_quantity: จำนวนสินค้ารวมทั้งหมด
        - low_stock_count: จำนวนสินค้าที่ quantity < reorder_point
    """
    try:
        # Get total products count
        total_products_result = await db.execute(
            select(func.count(Product.id))
        )
        total_products = total_products_result.scalar() or 0
        
        # Get total quantity sum
        total_quantity_result = await db.execute(
            select(func.sum(Product.quantity))
        )
        total_quantity = total_quantity_result.scalar() or 0
        
        # Get low stock count (quantity < reorder_point)
        low_stock_result = await db.execute(
            select(func.count(Product.id)).where(
                Product.quantity < Product.reorder_point
            )
        )
        low_stock_count = low_stock_result.scalar() or 0
        
        logger.info(
            f"Dashboard summary: {total_products} products, "
            f"{total_quantity} total quantity, {low_stock_count} low stock"
        )
        
        return DashboardSummary(
            total_products=total_products,
            total_quantity=total_quantity,
            low_stock_count=low_stock_count
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="เกิดข้อผิดพลาดในการดึงข้อมูลสรุป"
        )


@router.get("/recent-transactions", response_model=List[RecentTransaction])
@limiter.limit("100/minute")
@cache(expire=300)  # Cache for 5 minutes
async def get_recent_transactions(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Get 5 most recent transactions with items summary.
    Cached for 5 minutes to improve performance.
    
    Returns list of recent transactions with:
        - transaction_id
        - created_at
        - total_items
        - items_summary: list of product names
    """
    try:
        # Get 5 most recent transactions
        result = await db.execute(
            select(Transaction)
            .order_by(Transaction.created_at.desc())
            .limit(5)
        )
        transactions = result.scalars().all()
        
        # Build response with items summary
        response = []
        for transaction in transactions:
            # Get transaction items
            items_result = await db.execute(
                select(TransactionItem)
                .where(TransactionItem.transaction_id == transaction.id)
            )
            items = items_result.scalars().all()
            
            # Create items summary (list of product names with quantities)
            items_summary = [
                f"{item.product_name} ({item.quantity} {item.unit})"
                for item in items
            ]
            
            response.append(
                RecentTransaction(
                    transaction_id=transaction.id,
                    receipt_id=transaction.receipt_id,
                    created_at=transaction.created_at,
                    total_items=transaction.total_items,
                    items_summary=items_summary
                )
            )
        
        logger.info(f"Retrieved {len(response)} recent transactions")
        return response
        
    except Exception as e:
        logger.error(f"Error getting recent transactions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="เกิดข้อผิดพลาดในการดึงข้อมูล transactions ล่าสุด"
        )


@router.get("/low-stock-alerts", response_model=List[LowStockProduct])
@limiter.limit("100/minute")
@cache(expire=300)  # Cache for 5 minutes
async def get_low_stock_alerts(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Get products with low stock (quantity < reorder_point).
    Cached for 5 minutes to improve performance.
    
    Returns list of products that need reordering with:
        - product_id
        - product_name
        - quantity
        - unit
        - reorder_point
    """
    try:
        # Query products where quantity < reorder_point
        result = await db.execute(
            select(Product)
            .where(Product.quantity < Product.reorder_point)
            .order_by(Product.quantity.asc())  # Most urgent first
        )
        products = result.scalars().all()
        
        response = [
            LowStockProduct(
                product_id=product.id,
                product_name=product.name,
                quantity=product.quantity,
                unit=product.unit,
                reorder_point=product.reorder_point
            )
            for product in products
        ]
        
        logger.info(f"Found {len(response)} products with low stock")
        return response
        
    except Exception as e:
        logger.error(f"Error getting low stock alerts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="เกิดข้อผิดพลาดในการดึงข้อมูลสินค้าใกล้หมด"
        )


@router.get("/stock-trend", response_model=List[StockTrendData])
@limiter.limit("100/minute")
@cache(expire=300)  # Cache for 5 minutes
async def get_stock_trend(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Get stock trend for the last 7 days.
    Cached for 5 minutes to improve performance.
    
    Aggregates transactions by date and returns total items added per day.
    
    Returns list of:
        - date: วันที่ (YYYY-MM-DD)
        - total_items_added: จำนวนสินค้าที่เพิ่มในวันนั้น
    """
    try:
        # Calculate date range (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=6)  # 6 days ago + today = 7 days
        
        # Query transactions in date range
        result = await db.execute(
            select(Transaction)
            .where(
                and_(
                    Transaction.created_at >= start_date,
                    Transaction.created_at <= end_date
                )
            )
            .order_by(Transaction.created_at.asc())
        )
        transactions = result.scalars().all()
        
        # Aggregate by date
        daily_totals = {}
        for transaction in transactions:
            date_key = transaction.created_at.date().isoformat()
            
            # Get total quantity for this transaction
            items_result = await db.execute(
                select(func.sum(TransactionItem.quantity))
                .where(TransactionItem.transaction_id == transaction.id)
            )
            total_qty = items_result.scalar() or 0
            
            if date_key in daily_totals:
                daily_totals[date_key] += total_qty
            else:
                daily_totals[date_key] = total_qty
        
        # Build response for all 7 days (fill missing days with 0)
        response = []
        for i in range(7):
            current_date = (start_date + timedelta(days=i)).date()
            date_key = current_date.isoformat()
            
            response.append(
                StockTrendData(
                    date=date_key,
                    total_items_added=daily_totals.get(date_key, 0)
                )
            )
        
        logger.info(f"Retrieved stock trend for {len(response)} days")
        return response
        
    except Exception as e:
        logger.error(f"Error getting stock trend: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="เกิดข้อผิดพลาดในการดึงข้อมูลแนวโน้มสต็อก"
        )
