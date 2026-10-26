import asyncio
import json
import logging
from collections.abc import Iterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from agent.agent import run_agent, stream_agent, warmup_agent
from config.request import SyncSessionLocal, get_db
from crud import chat
from model.chat import Test, User
from schema.info import Userinfo
from utils.auth import get_current_user
from utils.response import success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


def _sse_line(payload: dict) -> str:
    """一帧 SSE：data 行 + 必须两个换行结尾。"""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.get("/health")
async def get_health():
    return {"code": 0, "message": "ok", "data": "ok"}


@router.post("/chat/warmup")
async def post_chat_warmup(current_user: User = Depends(get_current_user)):
    """登录后由前端再触发一次；后台预热，立即返回。"""
    try:
        asyncio.create_task(
            asyncio.to_thread(warmup_agent, current_user.id, current_user.role)
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("chat warmup schedule failed: %s", exc)
    return success_response(message="助手预热已开始", data={"ok": True})


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
    last_reply = run_agent(
        data.user_input, current_user.id, current_user.role
    )
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


@router.post("/chat/stream")
async def post_chat_stream(
    data: Userinfo,
    current_user: User = Depends(get_current_user),
):
    """
    SSE 打字效果。
    - stream_agent：跑 Agent、吐字典
    - event_gen：字典 → SSE 帧
    - StreamingResponse：推给浏览器
    流式只画；落库在 done 时写一次（不再二次 invoke）。
    """
    user_input = data.user_input
    user_id = current_user.id
    role = current_user.role

    def event_gen() -> Iterator[str]:
        final_answer = ""
        try:
            for item in stream_agent(user_input, user_id, role):
                if item.get("type") == "done":
                    final_answer = str(item.get("answer") or "")
                yield _sse_line(item)
        except Exception as exc:  # noqa: BLE001
            yield _sse_line({"type": "error", "content": str(exc)})
            return

        if not final_answer:
            return
        try:
            with SyncSessionLocal() as sync_db:
                sync_db.add(Test(user_input=user_input, agent_output=final_answer))
                sync_db.commit()
        except Exception as exc:  # noqa: BLE001
            yield _sse_line(
                {"type": "status", "content": f"回答已生成，但落库失败：{exc}"}
            )

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
