# back/cache/auth_cache.py
from config.cache_conf import get_str_cache, set_str_cache, delete_cache

TOKEN_TTL = 7 * 24 * 3600  # 和库里 token 7 天一致


def token_key(token: str) -> str:
    return f"auth:token:{token}"


async def get_cached_user_id(token: str) -> str | None:
    """读：Redis 里有没有这个 token → 返回 user_id 字符串"""
    return await get_str_cache(token_key(token))


async def set_cached_user_id(token: str, user_id: int) -> bool:
    """写：登录成功后把 token → user_id 放进 Redis"""
    return await set_str_cache(token_key(token), str(user_id), ex=TOKEN_TTL)


async def delete_cached_token(token: str) -> bool:
    """删：退出时清掉"""
    return await delete_cache(token_key(token))