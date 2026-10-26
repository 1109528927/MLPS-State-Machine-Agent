"""
等保工作台 Agent：工具查业务库 + 上下文加载 + Skills + RBAC + 短期记忆 + SSE。

用户身份经 LangGraph context 传入（勿用 ContextVar：工具常在别的线程执行，读不到）。
invoke / stream 时传 context=AgentUserContext(user_id, role)。
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NotRequired, cast

from dotenv import load_dotenv
from langchain.agents import AgentState, create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.chat_models import init_chat_model
from langchain.tools import ToolRuntime
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from agent.context import load_agent_context
from agent.rbac import get_gap_if_allowed, get_project_if_allowed, is_manager
from agent.rbac import list_visible_project_ids
from agent.skills import build_system_prompt
from config.request import SyncSessionLocal
from model.chat import GapItem, Project

# 本地读项目根 .env；Docker 里多由 compose 注入环境变量
_env = Path(__file__).resolve().parents[2] / ".env"
if _env.is_file():
    load_dotenv(_env, override=True)
load_dotenv(override=True)


# 当前登录用户随 invoke或stream 的 context 注入工具，让工具上下文具有用户的识别
@dataclass
class AgentUserContext:
    user_id: int
    role: str


def _require_user(runtime: ToolRuntime[AgentUserContext]) -> tuple[int, str]:
    ctx = runtime.context
    if ctx is None:
        raise RuntimeError(
            "未设置当前用户：请在 invoke/stream 时传入 context=AgentUserContext(...)"
        )
    return ctx.user_id, ctx.role


def make_user_context(user_id: int, role: str) -> AgentUserContext:
    return AgentUserContext(user_id=user_id, role=role)


# 模型
model = init_chat_model(
    model=os.getenv("DASHSCOPE_MODEL", "qwen-plus"),
    model_provider="openai",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
)


# 工具（全部只读；RBAC 统一走 agent.rbac)
@tool(parse_docstring=True)
def whoami(runtime: ToolRuntime[AgentUserContext]) -> str:
    """返回当前登录用户身份与数据范围。用户问「我是谁 / 我的权限」时调用。"""
    user_id, role = _require_user(runtime)
    ctx = load_agent_context(user_id, role)
    scope = "全部项目" if is_manager(role) else "仅被分配的项目"
    return (
        f"用户={ctx.username} | 工号={ctx.employee_no} | 角色={ctx.role_label}\n"
        f"数据范围={scope} | 可见项目数={ctx.visible_count}"
    )


@tool(parse_docstring=True)
def list_my_projects(
    runtime: ToolRuntime[AgentUserContext], name: str | None = None
) -> str:
    """查询当前用户可见的等保整改项目列表。用户问「我有哪些项目 / 项目列表」时必须调用。

    Args:
        name: 可选，按项目名称模糊搜索；不传则返回全部可见项目
    """
    user_id, role = _require_user(runtime)
    with SyncSessionLocal() as db:
        visible = list_visible_project_ids(db, user_id, role)
        if visible is not None and not visible:
            return "你当前没有被分配到任何项目。"
        stmt = select(Project).order_by(Project.create_at.desc())
        if visible is not None:
            stmt = stmt.where(Project.id.in_(visible))
        if name:
            stmt = stmt.where(Project.name.like(f"%{name}%"))
        rows = db.execute(stmt.limit(50)).scalars().all()
        if not rows:
            return "没有找到符合条件的项目。"
        lines = [
            f"id={p.id} | 名称={p.name} | 备注={p.remark or '-'}" for p in rows
        ]
        return "\n".join(lines)


@tool(parse_docstring=True)
def get_project_gap_stats(
    project_id: int, runtime: ToolRuntime[AgentUserContext]
) -> str:
    """查询某个项目下差距项各状态的数量统计。用户问「待整改有几条 / 状态统计」时必须调用。

    Args:
        project_id: 项目 id（可先用 list_my_projects 查到）
    """
    user_id, role = _require_user(runtime)
    with SyncSessionLocal() as db:
        project, err = get_project_if_allowed(db, user_id, role, project_id)
        if err:
            return err
        assert project is not None
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
def list_project_gaps(
    project_id: int,
    runtime: ToolRuntime[AgentUserContext],
    status: str | None = None,
) -> str:
    """列出某个项目下的差距项（可按状态过滤）。用户问「有哪些待整改 / 差距清单」时必须调用。

    Args:
        project_id: 项目 id
        status: 可选状态过滤，如 待整改、整改中、待复核、已通过、已关闭；不传则全部
    """
    user_id, role = _require_user(runtime)
    with SyncSessionLocal() as db:
        project, err = get_project_if_allowed(db, user_id, role, project_id)
        if err:
            return err
        assert project is not None
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
            f"id={g.id} | {g.title} | 状态={g.status} | 风险={g.risk_level or '-'} | 类别={g.category or '-'}"
            for g in rows
        ]
        return f"项目「{project.name}」差距项（最多30条）：\n" + "\n".join(lines)


@tool(parse_docstring=True)
def get_gap_detail(gap_id: int, runtime: ToolRuntime[AgentUserContext]) -> str:
    """查询单条差距项详情（原因、整改要求等）。用户问某条差距具体内容时调用。

    Args:
        gap_id: 差距项 id（可从 list_project_gaps 得到）
    """
    user_id, role = _require_user(runtime)
    with SyncSessionLocal() as db:
        gap, project, err = get_gap_if_allowed(db, user_id, role, gap_id)
        if err:
            return err
        assert gap is not None and project is not None
        return (
            f"差距 id={gap.id} | 项目「{project.name}」(id={project.id})\n"
            f"标题：{gap.title}\n"
            f"状态：{gap.status}\n"
            f"类别：{gap.category or '-'}\n"
            f"风险：{gap.risk_level or '-'}\n"
            f"原因：{gap.reason or '-'}\n"
            f"整改要求：{gap.requirement or '-'}"
        )


@tool(parse_docstring=True)
def get_my_workspace_summary(runtime: ToolRuntime[AgentUserContext]) -> str:
    """汇总当前用户可见项目的差距待办概况。用户问「总览 / 手头怎样 / 整体待整改」时调用。"""
    user_id, role = _require_user(runtime)
    with SyncSessionLocal() as db:
        visible = list_visible_project_ids(db, user_id, role)
        if visible is not None and not visible:
            return "你当前没有被分配项目，暂无待办汇总。"
        stmt = select(Project).order_by(Project.create_at.desc()).limit(20)
        if visible is not None:
            stmt = stmt.where(Project.id.in_(visible))
        projects = db.execute(stmt).scalars().all()
        if not projects:
            return "暂无项目。"
        lines = []
        total_pending = 0
        for p in projects:
            rows = db.execute(
                select(GapItem.status, func.count())
                .where(GapItem.project_id == p.id)
                .group_by(GapItem.status)
            ).all()
            mapping = {s: n for s, n in rows}
            pending = int(mapping.get("待整改", 0))
            doing = int(mapping.get("整改中", 0))
            review = int(mapping.get("待复核", 0))
            total_pending += pending
            lines.append(
                f"id={p.id} | {p.name} | 待整改={pending} 整改中={doing} 待复核={review}"
            )
        head = f"可见项目 {len(projects)} 个；待整改合计 {total_pending} 条。\n"
        return head + "\n".join(lines)


@tool(parse_docstring=True)
def search_session_memory(
    keyword: str, runtime: ToolRuntime[AgentUserContext]
) -> str:
    """在当前用户的短期会话记忆中搜索关键词（不查全库，避免越权看到他人记录）。

    Args:
        keyword: 要搜索的关键词
    """
    user_id, _role = _require_user(runtime)
    kw = (keyword or "").strip()
    if not kw:
        return "请提供关键词。"
    try:
        snap = agent.get_state(make_thread_config(user_id))
    except Exception:  
        return "当前会话记忆不可用，请直接提问业务问题。"
    values = snap.values if snap else {}
    messages = values.get("messages") or []
    hits: list[str] = []
    for m in messages:
        content = getattr(m, "content", "") or ""
        if not isinstance(content, str):
            content = str(content)
        if kw in content:
            role = getattr(m, "type", None) or m.__class__.__name__
            snippet = content.replace("\n", " ")[:120]
            hits.append(f"[{role}] {snippet}")
        if len(hits) >= 8:
            break
    if not hits:
        return f"本会话记忆中没有包含「{kw}」的内容。"
    return "本会话相关片段：\n" + "\n".join(hits)


# 结构化最终答案 
class AssistantReply(BaseModel):
    """助手给用户的最终结构化回答"""

    answer: str = Field(description="给用户看的中文回答，简洁说人话")
    based_on_tools: bool = Field(
        description="本轮是否依据了工具查询结果（查库/查会话）"
    )


# 短期记忆
checkpointer = InMemorySaver()


class ChatAgentState(AgentState):
    """扩展 state；短期记忆主要靠 messages + checkpointer。"""

    user_id: NotRequired[int]


def make_thread_config(user_id: int) -> RunnableConfig:
    """同一用户共用一个 thread，多轮续聊；换用户互不串记忆。"""
    return cast(
        RunnableConfig,
        {"configurable": {"thread_id": f"user-{user_id}"}},
    )


def build_turn_messages(
    user_input: str, user_id: int, role: str
) -> list[BaseMessage]:
    """每轮加载业务上下文，再拼用户问题（上下文加载）。"""
    ctx = load_agent_context(user_id, role)
    return [
        SystemMessage(content=ctx.to_prompt_block()),
        HumanMessage(content=user_input),
    ]


def _agent_input(user_input: str, user_id: int, role: str) -> Any:
    """拼 invoke/stream 入参；cast 掉 LangGraph 过严的 InputAgentState 检查。"""
    return {
        "messages": build_turn_messages(user_input, user_id, role),
        "user_id": user_id,
    }


agent = create_agent(
    model=model,
    tools=[
        whoami,
        list_my_projects,
        get_project_gap_stats,
        list_project_gaps,
        get_gap_detail,
        get_my_workspace_summary,
        search_session_memory,
    ],
    system_prompt=build_system_prompt(),
    checkpointer=checkpointer,
    state_schema=ChatAgentState,
    context_schema=AgentUserContext,
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


def _chunk_text(chunk) -> str:
    """从流式 chunk 里取出可展示的纯文本（跳过 tool_call 相关）。"""
    if chunk is None:
        return ""
    name = chunk.__class__.__name__
    if "Tool" in name:
        return ""
    tool_calls = getattr(chunk, "tool_calls", None) or []
    if tool_calls:
        return ""
    additional = getattr(chunk, "additional_kwargs", None) or {}
    if additional.get("tool_calls"):
        return ""
    content = getattr(chunk, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text") or ""))
        return "".join(parts)
    return ""


def _status_from_updates(data: dict) -> str | None:
    """从 updates 里提炼用户可读的步骤提示。"""
    if not isinstance(data, dict):
        return None
    if "tools" in data:
        return "正在调用业务查询工具…"
    if "model" in data or "agent" in data:
        return "正在组织回答…"
    return None


def stream_agent(user_input: str, user_id: int, role: str):
    """
    SSE 字典流：
      status — 步骤提示（不进气泡正文）
      token  — 增量字
      done   — 收尾 answer（前端勿再整段 append）
    """
    config = make_thread_config(user_id)
    user_ctx = make_user_context(user_id, role)
    streamed: list[str] = []
    yield {"type": "status", "content": "加载上下文…"}
    payload = _agent_input(user_input, user_id, role)
    yield {"type": "status", "content": "思考中…"}
    for mode, data in agent.stream(
        payload,
        config=config,
        context=user_ctx,
        stream_mode=["messages", "updates"],
    ):
        if mode == "updates":
            tip = _status_from_updates(data) if isinstance(data, dict) else None
            if tip:
                yield {"type": "status", "content": tip}
            continue

        if mode != "messages":
            continue
        if not isinstance(data, tuple) or len(data) < 1:
            continue
        chunk = data[0]
        meta = data[1] if len(data) > 1 and isinstance(data[1], dict) else {}
        node = str(meta.get("langgraph_node") or "")
        if node in ("tools", "ToolNode"):
            continue

        text = _chunk_text(chunk)
        if not text:
            continue
        streamed.append(text)
        yield {"type": "token", "content": text}

    snap = agent.get_state(config)
    values = snap.values if snap else {}
    answer = extract_reply(values) if values else ""
    if not answer:
        answer = "".join(streamed) or "（无回复）"
    yield {"type": "done", "answer": answer}


def run_agent(user_input: str, user_id: int, role: str) -> str:
    """非流式整包调用（保留给 /api/chat）。"""
    res = agent.invoke(
        _agent_input(user_input, user_id, role),
        config=make_thread_config(user_id),
        context=make_user_context(user_id, role),
    )
    return extract_reply(res)


# 预热（登录后 / 进程启动，不污染正式会话 thread）
_model_warmed = False
_warmup_users: set[int] = set()


def warmup_llm() -> None:
    """兼容旧调用：仅摸模型。"""
    warmup_agent()


def warmup_agent(user_id: int | None = None, role: str | None = None) -> None:
    """
    后台预热，降低用户第一次对话等待：
    1) 模型连通（进程内尽量只完整 ping 一次）
    2) 若带用户：加载业务上下文 + 走一遍 Agent 图（临时 thread_id，不进正式记忆）
    失败只打日志，不影响登录。
    """
    global _model_warmed
    try:
        if not _model_warmed:
            model.invoke([HumanMessage(content="ping")])
            _model_warmed = True
            print("[warmup] model ok")

        if user_id is None or role is None:
            return
        if user_id in _warmup_users:
            return
        _warmup_users.add(user_id)

        # 预加载可见项目等上下文（与首轮 build_turn_messages 同路径）
        load_agent_context(user_id, role)

        # 临时 thread，避免写入 user-{id} 正式会话记忆
        agent.invoke(
            _agent_input(
                "请调用 whoami，然后只回复两个字：就绪",
                user_id,
                role,
            ),
            config=cast(
                RunnableConfig,
                {"configurable": {"thread_id": f"warmup-{user_id}"}},
            ),
            context=make_user_context(user_id, role),
        )
        print(f"[warmup] agent ready user={user_id}")
    except Exception as exc:  # noqa: BLE001
        if user_id is not None:
            _warmup_users.discard(user_id)
        print(f"[warmup] failed: {exc}")
