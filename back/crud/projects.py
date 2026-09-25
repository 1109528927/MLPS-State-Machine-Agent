from fastapi import HTTPException
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from model.chat import GapItem, Project, GapActionLog, ProjectMember,User


def is_manager(role: str) -> bool:
    """经理可查看/操作全部项目（数据范围放开；动作仍受 ACTION_ROLES 限制）。"""
    return role == "manager"


async def list_project_ids_for_user(db: AsyncSession, user_id: int):
    """当前用户在成员表里有哪些项目 id。"""
    stmt = select(ProjectMember.project_id).where(ProjectMember.user_id == user_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def is_project_member(db: AsyncSession, user_id: int, project_id: int) -> bool:
    stmt = select(ProjectMember.id).where(
        ProjectMember.user_id == user_id,
        ProjectMember.project_id == project_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def getprojects(name: str | None, db: AsyncSession, user_id: int, role: str):
    """
    核查员：只返回成员表里的项目。
    经理：返回全部项目。
    """
    if is_manager(role):
        stmt = select(Project).order_by(Project.create_at.desc())
        if name:
            stmt = stmt.where(Project.name.like(f"%{name}%"))
        result = await db.execute(stmt)
        return result.scalars().all()

    project_ids = await list_project_ids_for_user(db, user_id)
    if not project_ids:
        return []

    stmt = (
        select(Project)
        .where(Project.id.in_(project_ids))
        .order_by(Project.create_at.desc())
    )
    if name:
        stmt = stmt.where(Project.name.like(f"%{name}%"))
    result = await db.execute(stmt)
    return result.scalars().all()


async def getlist_gaps(
    project_id: int | None,
    db: AsyncSession,
    user_id: int,
    role: str,
):
    """
    经理：不校验成员，可按 project_id 查任意项目（或不传则全库差距）。
    核查员：必须是成员。
    """
    if project_id is not None:
        if not is_manager(role) and not await is_project_member(db, user_id, project_id):
            raise HTTPException(status_code=403, detail="无权查看该项目的差距项")
        stmt = (
            select(GapItem)
            .where(GapItem.project_id == project_id)
            .order_by(GapItem.create_at.desc())
        )
    else:
        if is_manager(role):
            stmt = select(GapItem).order_by(GapItem.create_at.desc())
        else:
            project_ids = await list_project_ids_for_user(db, user_id)
            if not project_ids:
                return []
            stmt = (
                select(GapItem)
                .where(GapItem.project_id.in_(project_ids))
                .order_by(GapItem.create_at.desc())
            )

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_gap_by_id(db: AsyncSession, gap_id: int):
    stmt = select(GapItem).where(GapItem.id == gap_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def ensure_gap_access(
    db: AsyncSession,
    user_id: int,
    gap_id: int,
    role: str,
) -> GapItem:
    """差距存在；核查员须是项目成员，经理可访问全部。"""
    gap = await get_gap_by_id(db, gap_id)
    if not gap:
        raise HTTPException(status_code=404, detail="差距项不存在")
    if not is_manager(role) and not await is_project_member(db, user_id, gap.project_id):
        raise HTTPException(status_code=403, detail="无权操作该项目的差距项")
    return gap


TRANSITIONS = {
    ("待整改", "record"): "整改中",
    ("整改中", "submit"): "待复核",
    ("待复核", "reject"): "整改中",
    ("待复核", "approve"): "已通过",
    ("待整改", "close"): "已关闭",
}

# 谁能做哪些动作（与 user.role 字符串一致）
ACTION_ROLES = {
    "record": {"inspector"},
    "submit": {"inspector"},
    "reject": {"manager"},
    "approve": {"manager"},
    "close": {"manager"},
}


async def apply_gap_action(
    db: AsyncSession,
    gap_id: int,
    action: str,
    actor_id: int,
    role: str,
    comment: str | None = None,
):
    # 先数据范围（经理跳过成员限制），再角色，再状态机
    gap = await ensure_gap_access(db, actor_id, gap_id, role)

    allowed = ACTION_ROLES.get(action)
    if not allowed or role not in allowed:
        raise HTTPException(status_code=403, detail="当前角色无权执行该操作")

    key = (gap.status, action)
    if key not in TRANSITIONS:
        raise HTTPException(
            status_code=400,
            detail=f"当前状态「{gap.status}」不能执行「{action}」",
        )

    if action == "reject" and not (comment and comment.strip()):
        raise HTTPException(status_code=400, detail="退回必须填写原因")

    if action == "record" and not (comment and comment.strip()):
        raise HTTPException(status_code=400, detail="代录必须填写说明")

    from_status = gap.status
    to_status = TRANSITIONS[key]
    gap.status = to_status

    db.add(
        GapActionLog(
            gap_id=gap.id,
            actor_id=actor_id,
            action=action,
            from_status=from_status,
            to_status=to_status,
            comment=comment,
        )
    )
    await db.commit()
    await db.refresh(gap)
    return gap


async def list_gap_logs(db: AsyncSession, gap_id: int, user_id: int, role: str):
    await ensure_gap_access(db, user_id, gap_id, role)
    stmt = (
        select(GapActionLog)
        .where(GapActionLog.gap_id == gap_id)
        .order_by(GapActionLog.create_at.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def post_create_project(name:str,remark:str|None,db:AsyncSession,current_user_id:int,user_role:str):
    if(user_role!="manager"):
         raise HTTPException(status_code=403, detail="仅经理可新建项目")
    row = Project(
        name=name,
        remark=remark,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    member = ProjectMember(
        user_id=current_user_id,
        project_id=row.id,
    )
    db.add(member)
    await db.commit()
    return row

async def add_project_member(db: AsyncSession, user_id: int, project_id: int):
    project = (
        await db.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if await is_project_member(db, user_id, project_id):
        raise HTTPException(status_code=400, detail="该用户已在项目中")

    member = ProjectMember(user_id=user_id, project_id=project_id)
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member, project, user

async def get_all_user(db: AsyncSession, project_id: int):
    stmt = (
        select(ProjectMember, User)
        .join(User, User.id == ProjectMember.user_id)
        .where(ProjectMember.project_id == project_id)
    )
    result = await db.execute(stmt)
    return result.all()


async def remove_project_member(db: AsyncSession, user_id: int, project_id: int):
    if not await is_project_member(db, user_id, project_id):
        raise HTTPException(status_code=404, detail="该用户不在此项目中")

    await db.execute(
        delete(ProjectMember).where(
            ProjectMember.user_id == user_id,
            ProjectMember.project_id == project_id,
        )
    )
    await db.commit()
    return True 

async def get_gapscount(project_id:int,db:AsyncSession):
  stmt = (
    select(GapItem.status, func.count())
    .where(GapItem.project_id == project_id)
    .group_by(GapItem.status)
)
  result=await db.execute(stmt)
  rows = result.all()
  return {status: n for status, n in rows}

async def create_gaps(
    db: AsyncSession,
    project_id: int,
    title: str,
    user_id: int,
    role: str,
    category: str | None = None,
    risk_level: str | None = None,
    reason: str | None = None,
    requirement: str | None = None,
):
    project = (
        await db.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if not is_manager(role) and not await is_project_member(db, user_id, project_id):
        raise HTTPException(status_code=403, detail="无权在该项目录入差距")

    if not title or not title.strip():
        raise HTTPException(status_code=400, detail="标题不能为空")

    row = GapItem(
        project_id=project_id,
        title=title.strip(),
        status="待整改",
        category=category,
        risk_level=risk_level,
        reason=reason,
        requirement=requirement,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row
