"""Transaction models."""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import uuid


class Transaction(Base):
    """Transaction model for tracking inventory updates."""
    
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    receipt_id = Column(String, ForeignKey("receipts.id"), nullable=False, index=True)
    total_items = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationship to transaction items
    items = relationship("TransactionItem", back_populates="transaction", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, receipt_id={self.receipt_id}, total_items={self.total_items})>"


class TransactionItem(Base):
    """Transaction item model for individual products in a transaction."""
    
    __tablename__ = "transaction_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit = Column(String(50), nullable=False)
    original_text = Column(Text, nullable=False)  # Original text from receipt
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    transaction = relationship("Transaction", back_populates="items")
    
    def __repr__(self):
        return f"<TransactionItem(id={self.id}, product_name={self.product_name}, quantity={self.quantity})>"
