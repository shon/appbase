import redis

from settings import REDIS_HOST, REDIS_PORT, REDIS_DB

rconn = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
