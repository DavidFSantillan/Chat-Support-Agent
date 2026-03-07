""" cache_service.py - Cache management for the application
Whit Redis as the caching backend, this module provides functions to store and retrieve responses based on user queries
"""
import json
import logging
import redis.asyncio as redis
import hashlib
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class CacheService:
    """Cache service using Redis as the backend"""
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url,
                                           encodfing="utf-8",
                                           decode_responses=True )
    
    def make_key(self, query: str) -> str:
        """Create a cache key based on the user query using SHA256 hashing"""
        normalized_query = query.strip().lower()
        hash_key = hashlib.md5(normalized_query.encode("utf-8")).hexdigest()
        return f"cache:{hash_key}"
    
    async def get(self,query: str) -> dict | None:
        """Get a cached response for a given user query"""
        key = self.make_key(query)
        try:
            cached_data = await self.redis_client.get(key)
            if cached_data:
                logger.info(f"Cache hit for query: {query[:50]}")
                data =json.loads(cached_data)
                data["from_cache"] = True

                return data
            
            logger.info(f"Cache miss for query: {query}")
            return None
        except Exception as e:
            logger.error(f"Error accessing cache: {e}")
            return None
        
    async def set(self, query: str, response_data: dict):
        """Set a cache entry for a given user query and response data"""
        key = self.make_key(query)
        try:
            await self.redis_client.setex(
                name=key,
                time=settings.CACHE_TTL_SECONDS,
                value=json.dumps(response_data, ensure_ascii=False))
            logger.info(f"Cache stored for {settings.CACHE_TTL_SECONDS}s")
        except Exception as e:
            logger.error(f"Error setting cache: {e}")

    async def invalidate(self,query:str)->None:
        """Invalidate a cache entry for a given user query"""
        key = self.make_key(query)
        try:
            await self.redis_client.delete(key)
            logger.info(f"Cache invalidated for query: {query[:50]}")
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
    
    async def clear(self)-> int:
        """Clear all cache entries"""
        try:
            keys = await self.redis_client.keys("cache:*")
            if keys:
                deleted_count = await self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted_count} cache entries")
                return deleted_count
            logger.info("No cache entries to clear")
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0
    
    async def get_stats(self) -> dict:
        """Get cache statistics"""
        try:
            keys = await self.redis_client.keys("cache:*")
            info = await self.redis_client.info("stats")
            return {
                "cache_size": len(keys),
                "cache_keys": keys,
                "cache_hits": info.get("keyspace_hits", 0),
                "cache_misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "cache_size": 0,
                "cache_keys": []
            }