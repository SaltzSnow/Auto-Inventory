"""Retry utilities for external service calls"""
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
import logging
import httpx
from exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


# Retry decorator for API calls with exponential backoff
def retry_on_api_error(max_attempts: int = 3):
    """
    Decorator for retrying API calls with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
    
    Returns:
        Configured retry decorator
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            httpx.HTTPError,
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.ReadTimeout,
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        reraise=True
    )


# Retry decorator specifically for rate limiting (429 errors)
def retry_on_rate_limit(max_attempts: int = 5):
    """
    Decorator for retrying API calls when rate limited
    
    Args:
        max_attempts: Maximum number of retry attempts
    
    Returns:
        Configured retry decorator
    """
    def is_rate_limit_error(exception):
        """Check if exception is a rate limit error"""
        if isinstance(exception, httpx.HTTPStatusError):
            return exception.response.status_code == 429
        return False
    
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type(httpx.HTTPStatusError) & retry_if_exception_type(is_rate_limit_error),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        reraise=True
    )


# Combined retry decorator for all external service errors
def retry_external_service(max_attempts: int = 3):
    """
    Decorator for retrying external service calls with comprehensive error handling
    
    Args:
        max_attempts: Maximum number of retry attempts
    
    Returns:
        Configured retry decorator
    """
    def is_retryable_error(exception):
        """Check if exception is retryable"""
        # Retry on network errors
        if isinstance(exception, (
            httpx.HTTPError,
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.ReadTimeout,
        )):
            return True
        
        # Retry on specific HTTP status codes
        if isinstance(exception, httpx.HTTPStatusError):
            status_code = exception.response.status_code
            # Retry on 429 (rate limit), 500, 502, 503, 504 (server errors)
            return status_code in [429, 500, 502, 503, 504]
        
        return False
    
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=is_retryable_error,
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        reraise=True
    )
