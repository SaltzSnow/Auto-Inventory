"""Celery tasks for receipt processing."""
from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
import logging
from typing import List, Dict, Any

from celery_app import celery_app
from database import AsyncSessionLocal
from models.receipt import Receipt, ReceiptStatus
from services.openrouter_service import openrouter_service
from services.product_service import product_service
from schemas.receipt import ExtractedItem, MatchedProduct, ValidatedItem

logger = logging.getLogger(__name__)


class ReceiptProcessingTask(Task):
    """Custom task class for receipt processing with state tracking."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f"Task {task_id} failed: {exc}")
        
        # Update receipt status to failed
        receipt_id = args[0] if args else None
        if receipt_id:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            loop.run_until_complete(
                self._update_receipt_status(receipt_id, ReceiptStatus.FAILED, str(exc))
            )
    
    async def _update_receipt_status(
        self, 
        receipt_id: str, 
        status: ReceiptStatus, 
        error_message: str = None
    ):
        """Update receipt status in database."""
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(Receipt).where(Receipt.id == receipt_id)
                )
                receipt = result.scalar_one_or_none()
                
                if receipt:
                    receipt.status = status
                    if error_message:
                        receipt.error_message = error_message
                    await db.commit()
            except Exception as e:
                logger.error(f"Error updating receipt status: {str(e)}")
                await db.rollback()


@celery_app.task(
    bind=True,
    base=ReceiptProcessingTask,
    name="backend.tasks.receipt_tasks.process_receipt_task",
    max_retries=2,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True
)
def process_receipt_task(self, receipt_id: str) -> Dict[str, Any]:
    """
    Process receipt through AI pipeline.
    
    This task performs three main steps:
    1. Extract items from receipt image using Gemini Vision (33% progress)
    2. Match extracted items with products in inventory using vector search (66% progress)
    3. Validate and convert units using LLM (100% progress)
    
    Args:
        receipt_id: ID of the receipt to process
        
    Returns:
        Dictionary containing processing results with validated items
        
    Raises:
        Exception: If any step of the pipeline fails
    """
    logger.info(f"Starting receipt processing for receipt_id: {receipt_id}")
    
    # Run async processing in event loop
    # Use get_event_loop() instead of asyncio.run() to avoid event loop conflicts
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_process_receipt_async(self, receipt_id))


async def _process_receipt_async(task: Task, receipt_id: str) -> Dict[str, Any]:
    """Async implementation of receipt processing."""
    
    raw_ocr_content = None  # Initialize to None, will be set after OCR
    
    async with AsyncSessionLocal() as db:
        try:
            # Get receipt from database
            result = await db.execute(
                select(Receipt).where(Receipt.id == receipt_id)
            )
            receipt = result.scalar_one_or_none()
            
            if not receipt:
                raise Exception(f"Receipt not found: {receipt_id}")
            
            # Update status to processing
            receipt.status = ReceiptStatus.PROCESSING
            await db.commit()
            
            # Step 1: Extract items from image using Gemini Vision (33% progress)
            logger.info(f"Step 1: Extracting items from image for receipt {receipt_id}")
            task.update_state(
                state="PROGRESS",
                meta={
                    "progress": 33,
                    "current_step": "vision_extraction",
                    "message": "กำลังอ่านข้อมูลจากใบเสร็จด้วย AI..."
                }
            )
            
            extracted_items, raw_ocr_content = await openrouter_service.extract_items_from_image(
                receipt.image_url
            )
            
            # Save raw OCR content to receipt for debugging
            receipt.raw_text = raw_ocr_content
            await db.commit()
            
            if not extracted_items:
                raise Exception(f"No items extracted from receipt\n\nข้อมูลที่ OCR ได้: {raw_ocr_content}")
            
            logger.info(f"Extracted {len(extracted_items)} items from receipt {receipt_id}")
            
            # Step 2: Match products using vector search (66% progress)
            logger.info(f"Step 2: Matching products for receipt {receipt_id}")
            task.update_state(
                state="PROGRESS",
                meta={
                    "progress": 66,
                    "current_step": "matching",
                    "message": "กำลังจับคู่สินค้ากับคลัง..."
                }
            )
            
            matched_items: List[tuple[ExtractedItem, MatchedProduct]] = []
            unmatched_items: List[ExtractedItem] = []
            
            for extracted_item in extracted_items:
                matched_product = await product_service.find_matching_product(
                    db, 
                    extracted_item.name
                )
                
                if matched_product:
                    matched_items.append((extracted_item, matched_product))
                else:
                    unmatched_items.append(extracted_item)
                    logger.warning(
                        f"No matching product found for item: {extracted_item.name}"
                    )
            
            if not matched_items:
                error_msg = "No products could be matched from the receipt"
                if raw_ocr_content:
                    error_msg += f"\n\nข้อมูลที่ OCR ได้: {raw_ocr_content}"
                raise Exception(error_msg)
            
            logger.info(
                f"Matched {len(matched_items)} items, "
                f"{len(unmatched_items)} items unmatched for receipt {receipt_id}"
            )
            
            # Step 3: Validate and convert units (100% progress)
            logger.info(f"Step 3: Validating and converting units for receipt {receipt_id}")
            task.update_state(
                state="PROGRESS",
                meta={
                    "progress": 100,
                    "current_step": "validation",
                    "message": "กำลังยืนยันและแปลงหน่วย..."
                }
            )
            
            validated_items: List[ValidatedItem] = []
            
            for extracted_item, matched_product in matched_items:
                try:
                    validated_item = await openrouter_service.validate_and_convert(
                        matched_product,
                        extracted_item.original_text
                    )
                    validated_items.append(validated_item)
                except Exception as e:
                    logger.error(
                        f"Error validating item {extracted_item.name}: {str(e)}"
                    )
                    # Continue with other items even if one fails
                    continue
            
            if not validated_items:
                error_msg = "No items could be validated"
                if raw_ocr_content:
                    error_msg += f"\n\nข้อมูลที่ OCR ได้: {raw_ocr_content}"
                raise Exception(error_msg)
            
            logger.info(f"Validated {len(validated_items)} items for receipt {receipt_id}")
            
            # Prepare result data
            result_data = {
                "receipt_id": receipt_id,
                "items": [
                    {
                        "product_id": item.product_id,
                        "product_name": item.product_name,
                        "quantity": item.quantity,
                        "unit": item.unit,
                        "confidence": item.confidence,
                        "original_text": item.original_text
                    }
                    for item in validated_items
                ],
                "total_items": len(validated_items),
                "unmatched_items": [
                    {
                        "name": item.name,
                        "quantity": item.quantity,
                        "original_text": item.original_text
                    }
                    for item in unmatched_items
                ]
            }
            
            # Update receipt with results
            receipt.status = ReceiptStatus.PENDING_CONFIRMATION
            receipt.extracted_data = result_data
            receipt.error_message = None
            await db.commit()
            
            logger.info(f"Successfully processed receipt {receipt_id}")
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error processing receipt {receipt_id}: {str(e)}")
            
            # Prepare error message with raw OCR content if available
            error_message = str(e)
            if raw_ocr_content and "ข้อมูลที่ OCR ได้:" not in error_message:
                error_message += f"\n\nข้อมูลที่ OCR ได้: {raw_ocr_content}"
            
            # Update receipt status to failed
            try:
                result = await db.execute(
                    select(Receipt).where(Receipt.id == receipt_id)
                )
                receipt = result.scalar_one_or_none()
                
                if receipt:
                    receipt.status = ReceiptStatus.FAILED
                    receipt.error_message = error_message
                    await db.commit()
            except Exception as update_error:
                logger.error(f"Error updating receipt status: {str(update_error)}")
                await db.rollback()
            
            # Re-raise exception with enhanced error message
            raise Exception(error_message)
