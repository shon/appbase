import sys
import redis
import settings

rconn = redis.Redis(
    db=settings.REDIS_DB,
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=getattr(settings, 'REDIS_PASSWORD', None),
    decode_responses=True
)
