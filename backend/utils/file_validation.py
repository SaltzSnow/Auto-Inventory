"""File validation utilities for receipt uploads."""
import imghdr
import re
import uuid
from typing import Tuple
from pathlib import Path

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


class FileValidationError(Exception):
    """Exception raised for file validation errors."""
    pass


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize filename to prevent path traversal and other security issues.
    
    Args:
        filename: Original filename
        max_length: Maximum allowed filename length
        
    Returns:
        Sanitized filename
    """
    # Get file extension
    path = Path(filename)
    name = path.stem
    ext = path.suffix.lower()
    
    # Remove any path components (prevent path traversal)
    name = Path(name).name
    
    # Remove special characters, keep only alphanumeric, dash, underscore, and Thai characters
    name = re.sub(r'[^\w\s\-ก-๙]', '', name)
    
    # Replace spaces with underscores
    name = re.sub(r'\s+', '_', name)
    
    # Limit length (reserve space for extension and UUID)
    max_name_length = max_length - len(ext) - 37  # 37 = 1 underscore + 36 UUID chars
    if len(name) > max_name_length:
        name = name[:max_name_length]
    
    # Generate unique filename with UUID to prevent collisions
    unique_name = f"{name}_{uuid.uuid4()}{ext}"
    
    return unique_name


def validate_image_file(
    file_content: bytes,
    filename: str,
    max_size_mb: int = 10
) -> Tuple[bool, str]:
    """Validate uploaded image file.
    
    Args:
        file_content: Binary content of the file
        filename: Original filename
        max_size_mb: Maximum allowed file size in MB
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Raises:
        FileValidationError: If validation fails
    """
    # Check file size (max 10MB as per requirements)
    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        raise FileValidationError(
            f"ไฟล์มีขนาดใหญ่เกินไป ({file_size_mb:.2f}MB) ขนาดสูงสุดคือ {max_size_mb}MB"
        )
    
    # Check file extension
    allowed_extensions = {".jpg", ".jpeg", ".png"}
    file_ext = filename.lower().split(".")[-1] if "." in filename else ""
    if f".{file_ext}" not in allowed_extensions:
        raise FileValidationError(
            f"ประเภทไฟล์ไม่ถูกต้อง รองรับเฉพาะ .jpg และ .png"
        )
    
    # Verify actual file type matches extension using python-magic
    if HAS_MAGIC:
        try:
            mime = magic.from_buffer(file_content, mime=True)
            allowed_mimes = {"image/jpeg", "image/png"}
            
            if mime not in allowed_mimes:
                raise FileValidationError(
                    f"ไฟล์ไม่ใช่รูปภาพที่ถูกต้อง (MIME type: {mime}) กรุณาอัปโหลดไฟล์ .jpg หรือ .png"
                )
            
            # Verify extension matches MIME type
            if mime == "image/jpeg" and file_ext not in ["jpg", "jpeg"]:
                raise FileValidationError(
                    "นามสกุลไฟล์ไม่ตรงกับประเภทไฟล์จริง"
                )
            elif mime == "image/png" and file_ext != "png":
                raise FileValidationError(
                    "นามสกุลไฟล์ไม่ตรงกับประเภทไฟล์จริง"
                )
        except Exception as e:
            if isinstance(e, FileValidationError):
                raise
            # If magic fails, fall back to imghdr
            pass
    
    # Fallback: Verify actual image format using imghdr
    image_type = imghdr.what(None, h=file_content)
    if image_type not in ["jpeg", "png"]:
        raise FileValidationError(
            "ไฟล์ไม่ใช่รูปภาพที่ถูกต้อง กรุณาอัปโหลดไฟล์ .jpg หรือ .png"
        )
    
    return True, ""
