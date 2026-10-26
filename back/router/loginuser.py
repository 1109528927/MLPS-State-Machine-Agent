import asyncio
import logging

from config.request import get_db
from fastapi import APIRouter, Depends,HTTPException
from schema.loginuser import UserRequest,loginRequest
from sqlalchemy.ext.asyncio import AsyncSession
from crud.user import post_token, post_userinfo, add_user, post_login, list_all_users
from utils.response import success_response
from utils.auth import get_current_user
from model.chat import User
from cache.auth_cache import set_cached_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/user", tags=["login"])


def _schedule_agent_warmup(user_id: int, role: str) -> None:
    """登录后后台预热 Agent（模型+上下文+图），不阻塞登录响应。"""
    try:
        from agent.agent import warmup_agent

        asyncio.create_task(asyncio.to_thread(warmup_agent, user_id, role))
    except Exception as exc:  # noqa: BLE001
        logger.warning("schedule agent warmup failed: %s", exc)


@router.post("/login")
async def login(
    user_data: loginRequest,
    db: AsyncSession = Depends(get_db),
):
    loginuser=await post_login(db,user_data.username,user_data.password)
    if not loginuser:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    token=await post_token(db,loginuser.id)
    await set_cached_user_id(token, loginuser.id)
    data = {
    "token": token,
    "userInfo": {
        "id": loginuser.id,
        "username": loginuser.username,
        "employee_no": loginuser.employee_no,
        "role": loginuser.role,
    },
}
    # 先返回登录，再后台预热 Agent（别堵登录）
    _schedule_agent_warmup(loginuser.id, loginuser.role)
    return success_response(message="登录成功",data=data)


@router.get("/list")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """经理：分配成员时下拉选人。"""
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="仅经理可查看用户列表")
    rows = await list_all_users(db)
    data = [
        {
            "id": u.id,
            "username": u.username,
            "employee_no": u.employee_no,
            "role": u.role,
        }
        for u in rows
    ]
    return success_response(message="返回用户列表成功", data=data)


@router.post("/register")
async def register(
    user_data: UserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="仅经理可开通账号")
    row=await post_userinfo(db,user_data.username,user_data.password)
    if row:
        raise HTTPException(status_code=400, detail="用户已存在,请重新注册用户")
    newuser=await add_user(db,user_data.username,user_data.password,user_data.employee_no)
    data = {
    "userInfo": {
        "id": newuser.id,
        "username": newuser.username,
        "employee_no": newuser.employee_no,
        "role": newuser.role,
    },
}
    return success_response(message="注册成功",data=data)