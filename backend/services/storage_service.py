"""Storage service for receipt images."""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid
from utils.file_validation import sanitize_filename


class StorageService:
    """Service for managing receipt image storage."""
    
    def __init__(self, base_upload_dir: str = "backend/uploads"):
        """Initialize storage service.
        
        Args:
            base_upload_dir: Base directory for uploads
        """
        self.base_upload_dir = Path(base_upload_dir)
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)
    
    def save_receipt_image(self, file_content: bytes, original_filename: str) -> str:
        """Save receipt image to filesystem organized by date.
        
        Args:
            file_content: Binary content of the image file
            original_filename: Original filename from upload
            
        Returns:
            Relative path to saved file (e.g., "2025/10/20/uuid.jpg")
        """
        # Sanitize filename to prevent path traversal and security issues
        sanitized_filename = sanitize_filename(original_filename)
        
        # Create date-based directory structure
        now = datetime.now()
        date_path = Path(str(now.year)) / f"{now.month:02d}" / f"{now.day:02d}"
        full_dir = self.base_upload_dir / date_path
        full_dir.mkdir(parents=True, exist_ok=True)
        
        # Use sanitized filename (already includes UUID)
        file_path = full_dir / sanitized_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Return relative path from uploads directory
        relative_path = date_path / sanitized_filename
        return str(relative_path).replace("\\", "/")
    
    def get_image_url(self, filename: str) -> str:
        """Get URL for accessing receipt image.
        
        Args:
            filename: Relative path to image file
            
        Returns:
            URL path for accessing the image
        """
        return f"/api/receipts/image/{filename}"
    
    def get_image_path(self, filename: str) -> Optional[Path]:
        """Get full filesystem path to image.
        
        Args:
            filename: Relative path to image file
            
        Returns:
            Full path to image file, or None if not found
        """
        full_path = self.base_upload_dir / filename
        if full_path.exists() and full_path.is_file():
            return full_path
        return None


# Singleton instance
storage_service = StorageService()
