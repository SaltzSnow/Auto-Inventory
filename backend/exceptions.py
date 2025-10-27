"""Custom exception classes for the application"""
from typing import Any, Optional
from datetime import datetime


class AppException(Exception):
    """Base exception class for all application exceptions"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str = "INTERNAL_ERROR",
        details: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        super().__init__(self.message)
    
    def to_dict(self):
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "timestamp": datetime.now().isoformat()
        }


class NotFoundError(AppException):
    """Exception raised when a resource is not found"""
    
    def __init__(self, message: str = "ไม่พบข้อมูลที่ต้องการ", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=404,
            code="NOT_FOUND",
            details=details
        )


class ValidationError(AppException):
    """Exception raised when validation fails"""
    
    def __init__(self, message: str = "ข้อมูลไม่ถูกต้อง", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=400,
            code="VALIDATION_ERROR",
            details=details
        )


class ExternalServiceError(AppException):
    """Exception raised when external service call fails"""
    
    def __init__(
        self,
        message: str = "เกิดข้อผิดพลาดในการเชื่อมต่อกับบริการภายนอก",
        details: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            status_code=503,
            code="EXTERNAL_SERVICE_ERROR",
            details=details
        )


class DatabaseError(AppException):
    """Exception raised when database operation fails"""
    
    def __init__(
        self,
        message: str = "เกิดข้อผิดพลาดในการเข้าถึงฐานข้อมูล",
        details: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            status_code=500,
            code="DATABASE_ERROR",
            details=details
        )


class FileUploadError(AppException):
    """Exception raised when file upload fails"""
    
    def __init__(
        self,
        message: str = "เกิดข้อผิดพลาดในการอัปโหลดไฟล์",
        details: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            code="FILE_UPLOAD_ERROR",
            details=details
        )


class DuplicateError(AppException):
    """Exception raised when trying to create a duplicate resource"""
    
    def __init__(
        self,
        message: str = "ข้อมูลนี้มีอยู่ในระบบแล้ว",
        details: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            status_code=409,
            code="DUPLICATE_ERROR",
            details=details
        )


class EmbeddingFailureError(AppException):
    """Exception raised when embedding generation fails"""
    
    def __init__(
        self,
        message: str = "ไม่สามารถสร้าง embedding สำหรับสินค้าได้",
        details: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            status_code=422,  # Unprocessable Entity
            code="EMBEDDING_FAILURE",
            details=details
        )
