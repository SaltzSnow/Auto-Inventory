from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
import os
import time

# Import custom exceptions and logging
from exceptions import (
    AppException,
    NotFoundError,
    ValidationError,
    ExternalServiceError,
    DatabaseError,
    FileUploadError,
    DuplicateError
)
from utils.logging import setup_logging, get_logger, log_error, log_request
from utils.cache import cache_service
from middleware.security import RequestSizeLimitMiddleware, SecurityHeadersMiddleware

# Load environment variables
load_dotenv()

# Setup logging
setup_logging(log_level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="AI-Powered Inventory Management",
    description="ระบบจัดการคลังสินค้าด้วย AI ที่อ่านข้อมูลจากใบเสร็จอัตโนมัติ",
    version="1.0.0"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Startup event to initialize cache
@app.on_event("startup")
async def startup_event():
    """Initialize cache and other services on startup"""
    try:
        # Connect to Redis cache
        await cache_service.connect()
        
        # Initialize fastapi-cache2 for endpoint caching
        from redis import asyncio as aioredis
        redis_client = aioredis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            encoding="utf-8",
            decode_responses=True
        )
        FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
        
        logger.info("Cache services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize cache services: {str(e)}")


# Shutdown event to cleanup
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        await cache_service.disconnect()
        logger.info("Cache services disconnected")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware, max_size=10_000_000)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all API requests with timing"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration_ms = (time.time() - start_time) * 1000
    log_request(
        logger,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2)
    )
    
    return response


# Exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions"""
    log_error(
        logger,
        exc,
        context={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    log_error(
        logger,
        exc,
        context={
            "path": request.url.path,
            "method": request.method,
            "validation_errors": errors
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": "VALIDATION_ERROR",
            "message": "ข้อมูลที่ส่งมาไม่ถูกต้อง",
            "details": errors,
            "timestamp": None
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    log_error(
        logger,
        exc,
        context={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "INTERNAL_ERROR",
            "message": "เกิดข้อผิดพลาดภายในระบบ กรุณาลองใหม่อีกครั้ง",
            "details": None,
            "timestamp": None
        }
    )

# Import and register routers
from routers import products, receipts, transactions, dashboard

app.include_router(products.router)
app.include_router(receipts.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)

@app.get("/")
async def root():
    """Health check endpoint"""
    logger.info("root_endpoint_accessed")
    return {
        "status": "ok",
        "message": "AI-Powered Inventory Management API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    logger.info("health_check_accessed")
    return {
        "status": "healthy",
        "database": "not_configured",
        "redis": "not_configured"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
