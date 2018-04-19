import sys
import redis

from settings import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD

rconn = redis.Redis(
    db=REDIS_DB,
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)
