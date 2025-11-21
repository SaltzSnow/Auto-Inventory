"""Shared receipt processing pipeline logic."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.receipt import Receipt, ReceiptStatus
from schemas.receipt import ExtractedItem, MatchedProduct, ValidatedItem
from services.openrouter_service import openrouter_service
from services.product_service import product_service
from services.storage_service import storage_service

logger = logging.getLogger(__name__)

ProgressCallback = Optional[Callable[[int, str, str], None]]


async def run_receipt_pipeline(
    receipt_id: str,
    db: AsyncSession,
    progress_cb: ProgressCallback = None,
) -> dict[str, Any]:
    """Process a receipt through extraction → matching → validation steps."""

    receipt = await _get_receipt(db, receipt_id)
    if not receipt:
        raise Exception(f"Receipt not found: {receipt_id}")

    raw_ocr_content: Optional[str] = None

    try:
        receipt.status = ReceiptStatus.PROCESSING
        await db.commit()

        await _report(progress_cb, 33, "vision_extraction", "กำลังอ่านข้อมูลจากใบเสร็จด้วย AI...")
        extracted_items, raw_ocr_content = await openrouter_service.extract_items_from_image(
            receipt.image_url
        )
        receipt.raw_text = raw_ocr_content
        await db.commit()

        if not extracted_items:
            raise Exception(
                "No items extracted from receipt\n\nข้อมูลที่ OCR ได้: "
                f"{raw_ocr_content or 'N/A'}"
            )

        await _report(progress_cb, 66, "matching", "กำลังจับคู่สินค้ากับคลัง...")

        matched_items: list[tuple[ExtractedItem, MatchedProduct]] = []
        unmatched_items: list[ExtractedItem] = []

        for extracted_item in extracted_items:
            matched_product = await product_service.find_matching_product(db, extracted_item.name)
            if matched_product:
                matched_items.append((extracted_item, matched_product))
            else:
                unmatched_items.append(extracted_item)
                logger.warning("No matching product found for item: %s", extracted_item.name)

        if not matched_items:
            raise Exception(
                "No products could be matched from the receipt"
                + (f"\n\nข้อมูลที่ OCR ได้: {raw_ocr_content}" if raw_ocr_content else "")
            )

        await _report(progress_cb, 100, "validation", "กำลังยืนยันและแปลงหน่วย...")

        validated_items: list[ValidatedItem] = []
        for extracted_item, matched_product in matched_items:
            try:
                validated_item = await openrouter_service.validate_and_convert(
                    matched_product,
                    extracted_item.original_text,
                    extracted_item.quantity,
                )
                validated_items.append(validated_item)
            except Exception as exc:
                logger.error(
                    "Error validating item %s: %s", extracted_item.name, exc
                )

        if not validated_items:
            raise Exception(
                "No items could be validated"
                + (f"\n\nข้อมูลที่ OCR ได้: {raw_ocr_content}" if raw_ocr_content else "")
            )

        result_data = {
            "receipt_id": receipt_id,
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "confidence": item.confidence,
                    "original_text": item.original_text,
                }
                for item in validated_items
            ],
            "total_items": len(validated_items),
            "unmatched_items": [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "original_text": item.original_text,
                }
                for item in unmatched_items
            ],
            "image_url": _build_public_image_url(receipt),
        }

        receipt.status = ReceiptStatus.PENDING_CONFIRMATION
        receipt.extracted_data = result_data
        receipt.error_message = None
        await db.commit()

        return result_data

    except Exception as exc:  # noqa: BLE001
        logger.error("Error processing receipt %s: %s", receipt_id, exc)
        await _mark_failed(db, receipt_id, raw_ocr_content, str(exc))
        raise


async def _get_receipt(db: AsyncSession, receipt_id: str) -> Optional[Receipt]:
    result = await db.execute(select(Receipt).where(Receipt.id == receipt_id))
    return result.scalar_one_or_none()


async def _mark_failed(
    db: AsyncSession,
    receipt_id: str,
    raw_text: Optional[str],
    error: str,
) -> None:
    receipt = await _get_receipt(db, receipt_id)
    if not receipt:
        await db.rollback()
        return
    receipt.status = ReceiptStatus.FAILED
    message = error or "Unknown error"
    if raw_text and "ข้อมูลที่ OCR ได้:" not in message:
        message = f"{message}\n\nข้อมูลที่ OCR ได้: {raw_text}"
    receipt.error_message = message
    await db.commit()


async def _report(cb: ProgressCallback, progress: int, step: str, message: str) -> None:
    if not cb:
        return
    try:
        cb(progress, step, message)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Progress callback failed: %s", exc)


__all__ = ["run_receipt_pipeline"]


def _build_public_image_url(receipt: Receipt) -> str | None:
    image_path_str = receipt.image_url
    if not image_path_str:
        return None

    image_path = Path(image_path_str)
    base_dir = storage_service.base_upload_dir

    relative_path: Path | None = None

    try:
        relative_path = image_path.relative_to(base_dir)
    except ValueError:
        try:
            relative_path = image_path.resolve().relative_to(base_dir.resolve())
        except Exception:  # noqa: BLE001
            relative_path = image_path

    relative_str = str(relative_path).replace("\\", "/")
    return storage_service.get_image_url(relative_str)
