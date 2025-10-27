"""Product model."""
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from database import Base
import uuid


class Product(Base):
    """Product model with vector embedding for similarity search."""
    
    __tablename__ = "products"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    unit = Column(String(50), nullable=False)  # 'ชิ้น', 'กระป๋อง', 'ขวด', etc.
    quantity = Column(Integer, nullable=False, default=0)
    reorder_point = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=True)
    embedding = Column(Vector(1536), nullable=True)  # OpenAI ada-002 embedding dimension
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, quantity={self.quantity})>"
