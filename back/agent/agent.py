"""
等保工作台 Agent：工具查业务库 + 短期记忆（checkpointer）+ 可选结构化最终答案。

调用前请先 set_agent_user(user_id, role)，再带同一 thread_id 的 config 去 invoke。
"""
from __future__ import annotations

import os
from contextvars import ContextVar
from pathlib import Path
from typing import NotRequired

from dotenv import load_dotenv
from langchain.agents import AgentState, create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select

from config.request import SyncSessionLocal
from model.chat import GapItem, Project, ProjectMember, Test

# 本地读项目根 .env；Docker 里多由 compose 注入环境变量
_env = Path(__file__).resolve().parents[2] / ".env"
if _env.is_file():
    load_dotenv(_env, override=True)
load_dotenv(override=True)

# ---------- 当前登录用户（路由 invoke 前写入，工具内读取）----------
_agent_user: ContextVar[tuple[int, str] | None] = ContextVar(
    "agent_user", default=None
)


def set_agent_user(user_id: int, role: str):
    """路由里：invoke 前调用，把当前用户交给工具。"""
    return _agent_user.set((user_id, role))


def reset_agent_user(token) -> None:
    """路由里：invoke 后在 finally 里复位。"""
    _agent_user.reset(token)


def _require_user() -> tuple[int, str]:
    pair = _agent_user.get()
    if pair is None:
        raise RuntimeError("未设置当前用户：请先 set_agent_user 再调用 Agent")
    return pair


def _is_manager(role: str) -> bool:
    return role == "manager"


# ---------- 模型 ----------
model = init_chat_model(
    model=os.getenv("DASHSCOPE_MODEL", "qwen-plus"),
    model_provider="openai",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
)


# ---------- 工具（同步 Session，可在 Agent 工具循环里直接跑）----------
@tool(parse_docstring=True)
def list_my_projects(name: str | None = None) -> str:
    """查询当前用户可见的等保整改项目列表。用户问「我有哪些项目 / 项目列表」时必须调用。

    Args:
        name: 可选，按项目名称模糊搜索；不传则返回全部可见项目
    """
    user_id, role = _require_user()
    with SyncSessionLocal() as db:
        if _is_manager(role):
            stmt = select(Project).order_by(Project.create_at.desc())
        else:
            ids = (
                db.execute(
                    select(ProjectMember.project_id).where(
                        ProjectMember.user_id == user_id
                    )
                )
                .scalars()
                .all()
            )
            if not ids:
                return "你当前没有被分配到任何项目。"
            stmt = (
                select(Project)
                .where(Project.id.in_(list(ids)))
                .order_by(Project.create_at.desc())
            )
        if name:
            stmt = stmt.where(Project.name.like(f"%{name}%"))
        rows = db.execute(stmt).scalars().all()
        if not rows:
            return "没有找到符合条件的项目。"
        lines = [
            f"id={p.id} | 名称={p.name} | 备注={p.remark or '-'}" for p in rows
        ]
        return "\n".join(lines)


@tool(parse_docstring=True)
def get_project_gap_stats(project_id: int) -> str:
    """查询某个项目下差距项各状态的数量统计。用户问「待整改有几条 / 状态统计」时必须调用。

    Args:
        project_id: 项目 id（可先用 list_my_projects 查到）
    """
    user_id, role = _require_user()
    with SyncSessionLocal() as db:
        project = db.execute(
            select(Project).where(Project.id == project_id)
        ).scalar_one_or_none()
        if not project:
            return f"项目 id={project_id} 不存在。"
        if not _is_manager(role):
            member = db.execute(
                select(ProjectMember.id).where(
                    ProjectMember.user_id == user_id,
                    ProjectMember.project_id == project_id,
                )
            ).scalar_one_or_none()
            if not member:
                return f"你无权查看项目「{project.name}」(id={project_id})。"

        rows = db.execute(
            select(GapItem.status, func.count())
            .where(GapItem.project_id == project_id)
            .group_by(GapItem.status)
        ).all()
        if not rows:
            return f"项目「{project.name}」(id={project_id}) 下还没有差距项。"
        parts = [f"{status}={n}" for status, n in rows]
        total = sum(n for _, n in rows)
        return (
            f"项目「{project.name}」(id={project_id}) 差距统计：\n"
            + "；".join(parts)
            + f"；合计={total}"
        )


@tool(parse_docstring=True)
def list_project_gaps(project_id: int, status: str | None = None) -> str:
    """列出某个项目下的差距项（可按状态过滤）。用户问「有哪些待整改 / 差距清单」时必须调用。

    Args:
        project_id: 项目 id
        status: 可选状态过滤，如 待整改、整改中、待复核、已通过、已关闭；不传则全部
    """
    user_id, role = _require_user()
    with SyncSessionLocal() as db:
        project = db.execute(
            select(Project).where(Project.id == project_id)
        ).scalar_one_or_none()
        if not project:
            return f"项目 id={project_id} 不存在。"
        if not _is_manager(role):
            member = db.execute(
                select(ProjectMember.id).where(
                    ProjectMember.user_id == user_id,
                    ProjectMember.project_id == project_id,
                )
            ).scalar_one_or_none()
            if not member:
                return f"你无权查看项目「{project.name}」(id={project_id})。"

        stmt = (
            select(GapItem)
            .where(GapItem.project_id == project_id)
            .order_by(GapItem.create_at.desc())
            .limit(30)
        )
        if status:
            stmt = stmt.where(GapItem.status == status)
        rows = db.execute(stmt).scalars().all()
        if not rows:
            tip = f"（状态={status}）" if status else ""
            return f"项目「{project.name}」下没有差距项{tip}。"
        lines = [
            f"id={g.id} | {g.title} | 状态={g.status} | 风险={g.risk_level or '-'}"
            for g in rows
        ]
        return f"项目「{project.name}」差距项（最多30条）：\n" + "\n".join(lines)


@tool(parse_docstring=True)
def search_chat_history(keyword: str) -> str:
    """按关键词搜索本系统里保存过的聊天记录。用户要找「以前聊过什么」时调用。

    Args:
        keyword: 要搜索的关键词
    """
    with SyncSessionLocal() as db:
        stmt = (
            select(Test)
            .where(
                or_(
                    Test.user_input.like(f"%{keyword}%"),
                    Test.agent_output.like(f"%{keyword}%"),
                )
            )
            .limit(10)
        )
        rows = db.execute(stmt).scalars().all()
        if not rows:
            return f"没有找到包含「{keyword}」的聊天记录。"
        lines = [
            f"id={r.id} | 用户：{r.user_input} | 助手：{r.agent_output}"
            for r in rows
        ]
        return "\n".join(lines)


# ---------- 结构化最终答案（任务结束时收成字段；聊天仍取 answer）----------
class AssistantReply(BaseModel):
    """助手给用户的最终结构化回答"""

    answer: str = Field(description="给用户看的中文回答，简洁说人话")
    based_on_tools: bool = Field(
        description="本轮是否依据了工具查询结果（查库/查历史）"
    )


# ---------- 短期记忆：内存 Checkpointer + 按用户 thread_id ----------
checkpointer = InMemorySaver()


class ChatAgentState(AgentState):
    """扩展 state；短期记忆主要靠 messages + checkpointer。"""

    user_id: NotRequired[int]


def make_thread_config(user_id: int) -> dict:
    """同一用户共用一个 thread，多轮续聊；换用户互不串记忆。"""
    return {"configurable": {"thread_id": f"user-{user_id}"}}


agent = create_agent(
    model=model,
    tools=[
        list_my_projects,
        get_project_gap_stats,
        list_project_gaps,
        search_chat_history,
    ],
    system_prompt=(
        "你是等保整改跟踪工作台的智能助手。优先短答、说人话。\n"
        "规则：\n"
        "1. 问「我的项目 / 项目列表」→ 必须调用 list_my_projects。\n"
        "2. 问某项目「状态统计 / 待整改有几条」→ 必须调用 get_project_gap_stats。\n"
        "3. 问某项目「差距清单 / 有哪些待整改」→ 必须调用 list_project_gaps。\n"
        "4. 问「以前聊过什么」→ 调用 search_chat_history。\n"
        "5. 不知道项目 id 时，先 list_my_projects 再查统计/清单。\n"
        "6. 没有工具结果时，不要编造项目名、条数或状态；如实说明查不到。\n"
        "7. 最终用结构化字段 answer 回答用户。"
    ),
    checkpointer=checkpointer,
    state_schema=ChatAgentState,
    response_format=ToolStrategy(
        schema=AssistantReply,
        tool_message_content="已生成结构化回答",
    ),
    name="dengbao_assistant",
)


def extract_reply(result: dict) -> str:
    """优先用结构化 answer；没有则退回最后一条消息文本。"""
    structured = result.get("structured_response")
    if structured is not None:
        if isinstance(structured, AssistantReply):
            return structured.answer
        answer = getattr(structured, "answer", None)
        if answer:
            return str(answer)
        if isinstance(structured, dict) and structured.get("answer"):
            return str(structured["answer"])

    messages = result.get("messages") or []
    if not messages:
        return "（无回复）"
    content = messages[-1].content
    if isinstance(content, str):
        return content
    return str(content)
