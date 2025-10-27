"""Transaction service for managing inventory transactions."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from models.transaction import Transaction, TransactionItem
from models.receipt import Receipt
from schemas.receipt import ValidatedItem
from schemas.transaction import TransactionResponse, TransactionItemResponse
import logging

logger = logging.getLogger(__name__)


async def create_transaction(
    receipt_id: str,
    items: List[ValidatedItem],
    db: AsyncSession
) -> TransactionResponse:
    """
    Create a transaction record with transaction items.
    
    Uses database transaction (BEGIN/COMMIT) for atomicity.
    Links transaction with receipt_id.
    
    Args:
        receipt_id: ID of the receipt
        items: List of validated items from AI processing
        db: Database session
        
    Returns:
        TransactionResponse with created transaction and items
        
    Raises:
        ValueError: If receipt not found or items list is empty
    """
    if not items:
        raise ValueError("Items list cannot be empty")
    
    # Verify receipt exists
    result = await db.execute(
        select(Receipt).where(Receipt.id == receipt_id)
    )
    receipt = result.scalar_one_or_none()
    
    if not receipt:
        raise ValueError(f"Receipt with id {receipt_id} not found")
    
    try:
        # Create transaction record
        transaction = Transaction(
            receipt_id=receipt_id,
            total_items=len(items)
        )
        db.add(transaction)
        await db.flush()  # Flush to get transaction.id
        
        # Create transaction items
        transaction_items = []
        for item in items:
            transaction_item = TransactionItem(
                transaction_id=transaction.id,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                unit=item.unit,
                original_text=item.original_text
            )
            db.add(transaction_item)
            transaction_items.append(transaction_item)
        
        # Commit transaction
        await db.commit()
        await db.refresh(transaction)
        
        # Refresh all items to get their IDs and timestamps
        for item in transaction_items:
            await db.refresh(item)
        
        logger.info(
            f"Created transaction {transaction.id} with {len(items)} items for receipt {receipt_id}"
        )
        
        # Build response
        return TransactionResponse(
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
                for item in transaction_items
            ]
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating transaction for receipt {receipt_id}: {str(e)}")
        raise


async def get_transaction_by_id(
    transaction_id: str,
    db: AsyncSession
) -> Optional[TransactionResponse]:
    """
    Get a transaction by ID with all its items.
    
    Args:
        transaction_id: ID of the transaction
        db: Database session
        
    Returns:
        TransactionResponse or None if not found
    """
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        return None
    
    # Get transaction items
    items_result = await db.execute(
        select(TransactionItem).where(TransactionItem.transaction_id == transaction_id)
    )
    items = items_result.scalars().all()
    
    return TransactionResponse(
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
