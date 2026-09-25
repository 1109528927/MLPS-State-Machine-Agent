"""项目列表缓存策略：一人一份 project:list:{user_id}"""
from config.cache_conf import get_json_cache, set_json_cache, delete_cache

# 列表改得勤，TTL 用几分钟即可；改数据后还会主动 delete
PROJECT_LIST_TTL = 5 * 60


def project_list_key(user_id: int) -> str:
    return f"project:list:{user_id}"


async def get_cached_project_list(user_id: int):
    """读：该用户的项目列表；没有缓存返回 None"""
    return await get_json_cache(project_list_key(user_id))


async def set_cached_project_list(user_id: int, project_list) -> bool:
    """写：缓存该用户的项目列表（value 为可 JSON 序列化的 list）"""
    return await set_json_cache(
        project_list_key(user_id),
        project_list,
        ex=PROJECT_LIST_TTL,
    )


async def delete_cached_project_list(user_id: int) -> bool:
    """删：建项目 / 加人 / 删人后清掉，避免读到旧列表"""
    return await delete_cache(project_list_key(user_id))
