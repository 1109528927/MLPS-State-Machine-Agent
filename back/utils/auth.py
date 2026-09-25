from fastapi import Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from config.request import get_db
from crud.user import get_user_by_token
from model.chat import User
from cache.auth_cache import get_cached_user_id, set_cached_user_id

async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="未登录或缺少 token")

    # 前端：Authorization: Bearer <uuid>
    token = authorization
    if authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()

    if not token:
        raise HTTPException(status_code=401, detail="token 无效")
    cached_uid = await get_cached_user_id(token)
    if cached_uid is not None:
        user = (
            await db.execute(select(User).where(User.id == int(cached_uid)))
        ).scalar_one_or_none()
        if user:
            return user
        # 缓存脏了：继续走库

    # ② 缓存未命中（或脏了）→ 查 MySQL
    user = await get_user_by_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")

    # ③ 回填 Redis，下次认人可少打 user_token 表
    await set_cached_user_id(token, user.id)
    return user