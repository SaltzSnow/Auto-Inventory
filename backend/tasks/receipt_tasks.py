"""Celery tasks for receipt processing."""
from celery import Task
from sqlalchemy import select
import asyncio
import logging
from typing import Dict, Any

from celery_app import celery_app
from database import AsyncSessionLocal
from models.receipt import Receipt, ReceiptStatus
from services.receipt_pipeline import run_receipt_pipeline

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
    retry_jitter=True,
)
def process_receipt_task(self, receipt_id: str) -> Dict[str, Any]:
    """Process receipt through AI pipeline (executed by Celery worker)."""
    logger.info("Starting receipt processing for receipt_id: %s", receipt_id)

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_process_async(self, receipt_id))


async def _process_async(task: Task, receipt_id: str) -> Dict[str, Any]:
    async with AsyncSessionLocal() as db:
        def progress_cb(progress: int, step: str, message: str) -> None:
            task.update_state(
                state="PROGRESS",
                meta={
                    "progress": progress,
                    "current_step": step,
                    "message": message,
                },
            )

        return await run_receipt_pipeline(receipt_id, db, progress_cb)
