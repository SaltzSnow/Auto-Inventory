"""Receipt model."""
from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSON
from database import Base
import uuid
import enum


class ReceiptStatus(str, enum.Enum):
    """Receipt processing status."""
    PROCESSING = "processing"
    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class Receipt(Base):
    """Receipt model for tracking uploaded receipts and their processing status."""
    
    __tablename__ = "receipts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    image_url = Column(String(500), nullable=False)
    status = Column(SQLEnum(ReceiptStatus), nullable=False, default=ReceiptStatus.PROCESSING)
    raw_text = Column(Text, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Receipt(id={self.id}, status={self.status})>"
