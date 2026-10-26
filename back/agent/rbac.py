"""Agent 工具侧 RBAC：与业务成员表一致，拒权信息不泄露他人数据。"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from model.chat import GapItem, Project, ProjectMember


def is_manager(role: str) -> bool:
    return role == "manager"


def list_visible_project_ids(db: Session, user_id: int, role: str) -> list[int] | None:
    """
    经理：返回 None 表示「不限制 / 全库」。
    核查员：返回可见 project_id 列表（可能为空）。
    """
    if is_manager(role):
        return None
    ids = (
        db.execute(
            select(ProjectMember.project_id).where(ProjectMember.user_id == user_id)
        )
        .scalars()
        .all()
    )
    return list(ids)


def get_project_if_allowed(
    db: Session, user_id: int, role: str, project_id: int
) -> tuple[Project | None, str | None]:
    """
    校验项目是否存在且当前用户可访问。
    返回 (project, err)。err 非空则不可继续查该项目下任何差距细节。
    """
    project = db.execute(
        select(Project).where(Project.id == project_id)
    ).scalar_one_or_none()
    if not project:
        # 不区分「不存在」与「无权限」时可再收紧；教学项目保留不存在提示
        return None, f"项目 id={project_id} 不存在，或你无权查看。"

    if is_manager(role):
        return project, None

    member = db.execute(
        select(ProjectMember.id).where(
            ProjectMember.user_id == user_id,
            ProjectMember.project_id == project_id,
        )
    ).scalar_one_or_none()
    if not member:
        # 拒权：不透露项目真实名称（防枚举）
        return None, f"你无权查看项目 id={project_id}。请先确认自己被分配到该项目。"

    return project, None


def get_gap_if_allowed(
    db: Session, user_id: int, role: str, gap_id: int
) -> tuple[GapItem | None, Project | None, str | None]:
    """差距详情：必须先能访问其所属项目。"""
    gap = db.execute(select(GapItem).where(GapItem.id == gap_id)).scalar_one_or_none()
    if not gap:
        return None, None, f"差距项 id={gap_id} 不存在，或你无权查看。"
    project, err = get_project_if_allowed(db, user_id, role, gap.project_id)
    if err:
        return None, None, err
    return gap, project, None
