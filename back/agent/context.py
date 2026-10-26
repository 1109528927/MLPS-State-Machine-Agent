"""每轮调用前加载的业务上下文（注入给模型，减少盲目猜 id）。"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select

from agent.rbac import is_manager, list_visible_project_ids
from config.request import SyncSessionLocal
from model.chat import GapItem, Project, User


@dataclass
class AgentContext:
    user_id: int
    role: str
    username: str
    employee_no: str
    role_label: str
    project_lines: list[str]
    visible_count: int

    def to_prompt_block(self) -> str:
        role_hint = (
            "你是项目经理，可查看全部项目。"
            if is_manager(self.role)
            else "你是核查人员，只能查看被分配到的项目；无权项目一律拒绝编造。"
        )
        projects = (
            "\n".join(self.project_lines)
            if self.project_lines
            else "（当前没有可见项目）"
        )
        return (
            "[当前登录上下文 — 仅供工具选型与回答参考，禁止编造未列出的项目]\n"
            f"- 用户：{self.username}（工号 {self.employee_no}）\n"
            f"- 角色：{self.role_label}（{self.role}）\n"
            f"- 数据范围：{role_hint}\n"
            f"- 可见项目数：{self.visible_count}\n"
            f"- 可见项目摘要（最多 8 个）：\n{projects}\n"
            "若用户用项目名提问，先对照上述 id；不确定时调用 list_my_projects。"
        )


def load_agent_context(user_id: int, role: str) -> AgentContext:
    with SyncSessionLocal() as db:
        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        username = user.username if user else f"user-{user_id}"
        employee_no = (user.employee_no if user else "-") or "-"
        role_label = "项目经理" if is_manager(role) else "核查人员"

        visible_ids = list_visible_project_ids(db, user_id, role)
        stmt = select(Project).order_by(Project.create_at.desc()).limit(8)
        if visible_ids is not None:
            if not visible_ids:
                return AgentContext(
                    user_id=user_id,
                    role=role,
                    username=username,
                    employee_no=employee_no,
                    role_label=role_label,
                    project_lines=[],
                    visible_count=0,
                )
            stmt = (
                select(Project)
                .where(Project.id.in_(visible_ids))
                .order_by(Project.create_at.desc())
                .limit(8)
            )

        projects = db.execute(stmt).scalars().all()
        # 总数
        if visible_ids is None:
            total = db.execute(select(func.count()).select_from(Project)).scalar_one()
        else:
            total = len(visible_ids)

        lines: list[str] = []
        for p in projects:
            pending = db.execute(
                select(func.count())
                .select_from(GapItem)
                .where(GapItem.project_id == p.id, GapItem.status == "待整改")
            ).scalar_one()
            lines.append(
                f"  · id={p.id} | {p.name} | 待整改={pending}"
            )

        return AgentContext(
            user_id=user_id,
            role=role,
            username=username,
            employee_no=employee_no,
            role_label=role_label,
            project_lines=lines,
            visible_count=int(total),
        )
