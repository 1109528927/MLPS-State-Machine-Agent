from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from agent.agent import (
    agent,
    extract_reply,
    make_thread_config,
    reset_agent_user,
    set_agent_user,
)
from config.request import get_db
from crud import chat
from model.chat import User
from schema.info import Userinfo
from utils.auth import get_current_user

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/health")
async def get_health():
    return {"code": 0, "message": "ok", "data": "ok"}


@router.get("/chat/records")
async def get_rencent_info(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
):
    _ = current_user  # 鉴权：未登录不可拉历史
    rows = await chat.get_rencent_info(db, skip, limit)
    data = []
    for r in rows:
        data.append(
            {
                "id": r.id,
                "user_input": r.user_input,
                "agent_output": r.agent_output,
                "create_at": r.create_at,
            }
        )
    return {"code": 0, "message": "ok", "data": data}


@router.post("/chat")
async def post_info(
    data: Userinfo,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ① 把当前用户写入 ContextVar，工具里才能做权限过滤
    token = set_agent_user(current_user.id, current_user.role)
    try:
        # ② 同一 user 的 thread_id → 短期记忆续聊
        res = agent.invoke(
            {
                "messages": [HumanMessage(content=data.user_input)],
                "user_id": current_user.id,
            },
            config=make_thread_config(current_user.id),
        )
        last_reply = extract_reply(res)
    finally:
        reset_agent_user(token)

    row = await chat.post_inset_info(db, data.user_input, last_reply)
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "id": row.id,
            "user_input": row.user_input,
            "agent_output": row.agent_output,
            "create_at": row.create_at,
        },
    }
