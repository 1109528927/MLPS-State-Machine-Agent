"""差距状态统计缓存：一项目一份 gap:count:{project_id}"""
from config.cache_conf import get_json_cache, set_json_cache, delete_cache

# 统计会随 action / 录入变，TTL 短一点；写后也会 delete
GAP_COUNT_TTL = 5 * 60


def gap_count_key(project_id: int) -> str:
    return f"gap:count:{project_id}"


async def get_cached_gap_count(project_id: int):
    """读：该项目各状态数量 dict；没有缓存返回 None"""
    return await get_json_cache(gap_count_key(project_id))


async def set_cached_gap_count(project_id: int, counts) -> bool:
    """写：缓存状态统计（value 为可 JSON 序列化的 dict）"""
    return await set_json_cache(
        gap_count_key(project_id),
        counts,
        ex=GAP_COUNT_TTL,
    )


async def delete_cached_gap_count(project_id: int) -> bool:
    """删：状态变更 / 新建差距后清掉，避免读到旧统计"""
    return await delete_cache(gap_count_key(project_id))
