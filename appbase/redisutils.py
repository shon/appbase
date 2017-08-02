import sys
import redis

from settings import REDIS_HOST, REDIS_PORT, REDIS_DB

if sys.version[0] == '2':
    rconn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
else:
    rconn = redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
