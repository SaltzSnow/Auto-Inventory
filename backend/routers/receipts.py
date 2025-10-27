"""Receipt processing API endpoints."""
from fastapi import APIRouter, HTTPException, Path as PathParam, UploadFile, File, Depends, Request
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Dict, Any
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging

from services.storage_service import storage_service
from services.transaction_service import create_transaction
from services.product_service import product_service
from utils.file_validation import validate_image_file, FileValidationError
from database import get_db
from models.receipt import Receipt, ReceiptStatus
from schemas.receipt import ValidatedItem
from tasks.receipt_tasks import process_receipt_task
from celery_app import celery_app

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/receipts", tags=["receipts"])


# Pydantic schemas for request/response
class UploadReceiptResponse(BaseModel):
    """Response for receipt upload."""
    receipt_id: str
    task_id: str
    message: str


class TaskStatusResponse(BaseModel):
    """Response for task status query."""
    status: str
    progress: int
    current_step: str
    result: Dict[str, Any] | None = None
    error: str | None = None


class ConfirmReceiptItem(BaseModel):
    """Item to confirm in receipt."""
    product_id: str
    product_name: str
    quantity: int
    unit: str
    original_text: str


class ConfirmReceiptRequest(BaseModel):
    """Request to confirm receipt items."""
    receipt_id: str
    items: List[ConfirmReceiptItem]


class ConfirmReceiptResponse(BaseModel):
    """Response for receipt confirmation."""
    transaction_id: str
    total_items: int
    message: str


@router.post("/upload", response_model=UploadReceiptResponse)
@limiter.limit("100/minute")
async def upload_receipt(
    request: Request,
    file: UploadFile = File(..., description="Receipt image file (.jpg or .png)"),
    db: AsyncSession = Depends(get_db)
):
    """Upload receipt image and trigger AI processing.
    
    This endpoint:
    1. Validates the uploaded file (type, size, format)
    2. Saves the image to storage
    3. Creates a Receipt record in the database
    4. Triggers a Celery task for AI processing
    5. Returns the task_id for status polling
    
    Args:
        file: Uploaded image file
        db: Database session
        
    Returns:
        UploadReceiptResponse with receipt_id and task_id
        
    Raises:
        HTTPException: If validation fails or processing error occurs
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Validate file
        try:
            validate_image_file(file_content, file.filename)
        except FileValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Save file to storage
        relative_path = storage_service.save_receipt_image(file_content, file.filename)
        
        # Get full path for AI processing
        full_path = storage_service.get_image_path(relative_path)
        if not full_path:
            raise HTTPException(
                status_code=500,
                detail="เกิดข้อผิดพลาดในการบันทึกไฟล์"
            )
        
        # Create Receipt record
        receipt = Receipt(
            image_url=str(full_path),
            status=ReceiptStatus.PROCESSING
        )
        
        db.add(receipt)
        await db.flush()
        await db.refresh(receipt)
        
        logger.info(f"Created receipt record: {receipt.id}")
        
        # Trigger Celery task for AI processing
        task = process_receipt_task.apply_async(args=[receipt.id])
        
        logger.info(f"Triggered Celery task: {task.id} for receipt: {receipt.id}")
        
        return UploadReceiptResponse(
            receipt_id=receipt.id,
            task_id=task.id,
            message="อัปโหลดสำเร็จ กำลังประมวลผลด้วย AI..."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading receipt: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"เกิดข้อผิดพลาดในการอัปโหลด: {str(e)}"
        )


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
@limiter.limit("100/minute")
async def get_task_status(request: Request, task_id: str):
    """Get status of receipt processing task.
    
    This endpoint queries the Celery task status and returns:
    - Current processing status (PENDING, PROGRESS, SUCCESS, FAILURE)
    - Progress percentage (0-100)
    - Current processing step
    - Result data (if completed)
    - Error message (if failed)
    
    Args:
        task_id: Celery task ID
        
    Returns:
        TaskStatusResponse with current task status
        
    Raises:
        HTTPException: If task not found
    """
    try:
        # Get task result from Celery
        task_result = celery_app.AsyncResult(task_id)
        
        # Map Celery states to response
        if task_result.state == "PENDING":
            return TaskStatusResponse(
                status="pending",
                progress=0,
                current_step="queued",
                result=None,
                error=None
            )
        
        elif task_result.state == "PROGRESS":
            # Get progress info from task meta
            meta = task_result.info or {}
            return TaskStatusResponse(
                status="processing",
                progress=meta.get("progress", 0),
                current_step=meta.get("current_step", "unknown"),
                result=None,
                error=None
            )
        
        elif task_result.state == "SUCCESS":
            return TaskStatusResponse(
                status="completed",
                progress=100,
                current_step="done",
                result=task_result.result,
                error=None
            )
        
        elif task_result.state == "FAILURE":
            error_message = str(task_result.info) if task_result.info else "Unknown error"
            return TaskStatusResponse(
                status="failed",
                progress=0,
                current_step="error",
                result=None,
                error=error_message
            )
        
        else:
            # Unknown state
            return TaskStatusResponse(
                status="unknown",
                progress=0,
                current_step="unknown",
                result=None,
                error=None
            )
            
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"เกิดข้อผิดพลาดในการตรวจสอบสถานะ: {str(e)}"
        )


@router.post("/confirm", response_model=ConfirmReceiptResponse)
@limiter.limit("100/minute")
async def confirm_receipt(
    request: Request,
    data: ConfirmReceiptRequest,
    db: AsyncSession = Depends(get_db)
):
    """Confirm receipt items and update inventory.
    
    This endpoint:
    1. Validates the receipt exists and is in PENDING_CONFIRMATION status
    2. Creates a Transaction record with TransactionItem records
    3. Updates product quantities in inventory atomically
    4. Checks for low stock alerts
    5. Updates receipt status to CONFIRMED
    
    Args:
        data: Confirmation request with receipt_id and items
        db: Database session
        
    Returns:
        ConfirmReceiptResponse with transaction details
        
    Raises:
        HTTPException: If receipt not found, invalid status, or update fails
    """
    try:
        # Get receipt
        result = await db.execute(
            select(Receipt).where(Receipt.id == data.receipt_id)
        )
        receipt = result.scalar_one_or_none()
        
        if not receipt:
            raise HTTPException(
                status_code=404,
                detail="ไม่พบใบเสร็จที่ระบุ"
            )
        
        if receipt.status != ReceiptStatus.PENDING_CONFIRMATION:
            raise HTTPException(
                status_code=400,
                detail=f"สถานะใบเสร็จไม่ถูกต้อง (ปัจจุบัน: {receipt.status})"
            )
        
        # Convert request items to ValidatedItem format
        validated_items = [
            ValidatedItem(
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                unit=item.unit,
                confidence=1.0,  # User confirmed, so confidence is 100%
                original_text=item.original_text
            )
            for item in data.items
        ]
        
        # Update inventory using product service
        low_stock_products = await product_service.update_inventory(db, validated_items)
        
        if low_stock_products:
            logger.warning(
                f"Low stock alert for {len(low_stock_products)} products: "
                f"{[p['product_name'] for p in low_stock_products]}"
            )
        
        # Create transaction using transaction service
        transaction_response = await create_transaction(
            receipt_id=receipt.id,
            items=validated_items,
            db=db
        )
        
        # Update receipt status
        receipt.status = ReceiptStatus.CONFIRMED
        await db.commit()
        
        logger.info(
            f"Confirmed receipt {receipt.id} with {len(data.items)} items. "
            f"Transaction: {transaction_response.id}"
        )
        
        return ConfirmReceiptResponse(
            transaction_id=transaction_response.id,
            total_items=transaction_response.total_items,
            message="บันทึกข้อมูลสำเร็จ อัปเดตสต็อกเรียบร้อยแล้ว"
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error confirming receipt: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error confirming receipt: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {str(e)}"
        )


@router.get("/image/{filename:path}")
@limiter.limit("100/minute")
async def get_receipt_image(
    request: Request,
    filename: str = PathParam(..., description="Relative path to receipt image")
):
    """Serve receipt image file.
    
    Args:
        filename: Relative path to image (e.g., "2025/10/20/uuid.jpg")
        
    Returns:
        Image file
        
    Raises:
        HTTPException: If image not found
    """
    # Get full path to image
    image_path = storage_service.get_image_path(filename)
    
    if not image_path:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบรูปภาพที่ระบุ"
        )
    
    # Determine media type
    suffix = image_path.suffix.lower()
    media_type = "image/jpeg" if suffix in [".jpg", ".jpeg"] else "image/png"
    
    return FileResponse(
        path=str(image_path),
        media_type=media_type
    )
