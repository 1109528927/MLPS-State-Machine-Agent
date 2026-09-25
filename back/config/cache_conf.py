import json
import os
from typing import Any, cast

import redis.asyncio as redis

# 本地默认 localhost；Docker Compose 里 REDIS_HOST=redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
)

# config/cache_conf.py（要点）

# 读字符串
async def get_str_cache(key: str) -> str | None:
    return cast(str | None, await redis_client.get(key))

# 读 list/dict
async def get_json_cache(key: str)-> Any|None:
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
    return None

async def set_str_cache(key: str, value: str, ex=None) -> bool:
    return bool(await redis_client.set(key, value, ex=ex))
async def set_json_cache(key: str, value, ex=None) -> bool:
    return bool(await redis_client.set(key, json.dumps(value), ex=ex))
async def delete_cache(key: str) -> bool:
    return bool(await redis_client.delete(key))