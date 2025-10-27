"""Redis cache utility for caching embeddings and API responses."""
import os
import json
from typing import Optional, List
from redis import asyncio as aioredis
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Service for Redis caching operations."""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client: Optional[aioredis.Redis] = None
    
    async def connect(self):
        """Connect to Redis."""
        if not self.redis_client:
            try:
                self.redis_client = await aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("Disconnected from Redis cache")
    
    async def get_embedding(self, product_name: str) -> Optional[List[float]]:
        """
        Get cached embedding for a product name.
        
        Args:
            product_name: Name of the product
            
        Returns:
            List of floats representing the embedding, or None if not cached
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = f"embedding:{product_name}"
            cached_value = await self.redis_client.get(cache_key)
            
            if cached_value:
                logger.info(f"Cache hit for embedding: {product_name}")
                return json.loads(cached_value)
            
            logger.debug(f"Cache miss for embedding: {product_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached embedding: {str(e)}")
            return None
    
    async def set_embedding(
        self, 
        product_name: str, 
        embedding: List[float],
        ttl: int = 7 * 24 * 60 * 60  # 7 days in seconds
    ) -> bool:
        """
        Cache an embedding for a product name.
        
        Args:
            product_name: Name of the product
            embedding: Embedding vector to cache
            ttl: Time to live in seconds (default: 7 days)
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            cache_key = f"embedding:{product_name}"
            await self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(embedding)
            )
            logger.info(f"Cached embedding for: {product_name} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error caching embedding: {str(e)}")
            return False
    
    async def delete_embedding(self, product_name: str) -> bool:
        """
        Delete cached embedding for a product name.
        
        Args:
            product_name: Name of the product
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            cache_key = f"embedding:{product_name}"
            await self.redis_client.delete(cache_key)
            logger.info(f"Deleted cached embedding for: {product_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting cached embedding: {str(e)}")
            return False


# Singleton instance
cache_service = CacheService()
