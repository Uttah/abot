import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from redis.asyncio import Redis

from ..config import RATE_LIMIT_MESSAGES, RATE_LIMIT_PERIOD, REDIS_URL

logger = logging.getLogger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    """Rate limiting middleware using Redis."""
    
    def __init__(self):
        self.redis: Redis | None = None
        self.prefix = "throttle"
    
    async def _get_redis(self) -> Redis:
        if self.redis is None:
            self.redis = Redis.from_url(REDIS_URL)
        return self.redis
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Only throttle messages
        if not isinstance(event, Message):
            return await handler(event, data)
        
        if not event.from_user:
            return await handler(event, data)
        
        user_id = event.from_user.id
        key = f"{self.prefix}:{user_id}"
        
        try:
            redis = await self._get_redis()
            
            # Get current count
            current = await redis.get(key)
            
            if current is None:
                # First message - set counter with TTL
                await redis.setex(key, RATE_LIMIT_PERIOD, 1)
            elif int(current) >= RATE_LIMIT_MESSAGES:
                # Rate limit exceeded
                ttl = await redis.ttl(key)
                logger.warning(
                    "Rate limit exceeded for user %s (count: %s, ttl: %s)",
                    user_id, current, ttl
                )
                await event.answer(
                    f"⏳ Слишком много сообщений. Подождите {ttl} секунд."
                )
                return  # Don't call handler
            else:
                # Increment counter
                await redis.incr(key)
        
        except Exception as e:
            # If Redis fails, allow the message through
            logger.error("Throttling middleware error: %s", e)
        
        return await handler(event, data)
