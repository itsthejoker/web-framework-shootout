import sys
import uuid

import redis
from addict import Dict

context = Dict()

try:
    # the only reason we're running on db 1 is because I have another project
    # on db 0
    redis_server = redis.StrictRedis(host='localhost', port=6379, db=1)
    redis_server.ping()
except redis.exceptions.ConnectionError:
    print("Redis server is not running! Exiting!")
    sys.exit(1)

context.redis = redis_server

if context.redis.get('pass_the_salt') is None:
    context.redis.set('pass_the_salt', uuid.uuid4().hex)

context.app_name = "Votearama!"
