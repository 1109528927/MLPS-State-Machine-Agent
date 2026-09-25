from config.request import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from utils.response import success_response
from utils.auth import get_current_user
from model.chat import User
from schema.gap import GapActionRequest, GapCreateRequest
from schema.info import ProjectRequest, ProjectMemberRequest
from cache.project_cache import (
    get_cached_project_list,
    set_cached_project_list,
    delete_cached_project_list,
)
from cache.gap_cache import (
    get_cached_gap_count,
    set_cached_gap_count,
    delete_cached_gap_count,
)
from crud.projects import (
    getprojects,
    getlist_gaps,
    apply_gap_action,
    list_gap_logs,
    post_create_project,
    add_project_member,
    get_all_user,
    remove_project_member,
    get_gapscount,
    create_gaps,
)

router = APIRouter(prefix="/api/project", tags=["list"])


def _project_rows_to_data(rows) -> list[dict]:
    """ORM 行 → 可进 Redis / 返回前端的 dict 列表"""
    data = []
    for r in rows:
        data.append(
            {
                "id": r.id,
                "name": r.name,
                "remark": r.remark,
                "create_at": r.create_at.isoformat() if r.create_at else None,
            }
        )
    return data


@router.get("/list")
async def getprojectlist(
    name: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 有搜索词：不走缓存，直接查库
    if name:
        rows = await getprojects(name, db, current_user.id, current_user.role)
        return success_response(
            message="返回项目列表成功",
            data=_project_rows_to_data(rows),
        )

    # 无搜索：旁路读缓存
    cached = await get_cached_project_list(current_user.id)
    if cached is not None:
        return success_response(message="返回项目列表成功", data=cached)

    rows = await getprojects(None, db, current_user.id, current_user.role)
    data = _project_rows_to_data(rows)
    await set_cached_project_list(current_user.id, data)
    return success_response(message="返回项目列表成功", data=data)


@router.get("/list/gap")
async def getlists_gap(
    project_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = await getlist_gaps(
        project_id, db, user_id=current_user.id, role=current_user.role
    )
    data = []
    for r in rows:
        data.append(
            {
                "id": r.id,
                "project_id": r.project_id,
                "title": r.title,
                "status": r.status,
                "category": r.category,
                "risk_level": r.risk_level,
                "reason": r.reason,
                "requirement": r.requirement,
                "create_at": r.create_at,
            }
        )
    return success_response(message="返回差距项成功", data=data)


@router.get("/gap/{gap_id}/logs")
async def gap_logs(
    gap_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = await list_gap_logs(
        db, gap_id, user_id=current_user.id, role=current_user.role
    )
    data = []
    for r in rows:
        data.append(
            {
                "id": r.id,
                "gap_id": r.gap_id,
                "actor_id": r.actor_id,
                "action": r.action,
                "from_status": r.from_status,
                "to_status": r.to_status,
                "comment": r.comment,
                "create_at": r.create_at,
            }
        )
    return success_response(message="返回操作历史成功", data=data)


@router.post("/gap/{gap_id}/action")
async def gap_action(
    gap_id: int,
    body: GapActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    gap = await apply_gap_action(
        db,
        gap_id=gap_id,
        action=body.action,
        actor_id=current_user.id,
        role=current_user.role,
        comment=body.comment,
    )
    await delete_cached_gap_count(gap.project_id)
    return success_response(
        message="状态更新成功",
        data={
            "id": gap.id,
            "status": gap.status,
            "project_id": gap.project_id,
            "title": gap.title,
            "actor_id": current_user.id,
            "role": current_user.role,
        },
    )


@router.post("/create")
async def post_cre_project(
    body: ProjectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id
    user_role = current_user.role
    res = await post_create_project(body.name, body.remark, db, user_id, user_role)
    await delete_cached_project_list(user_id)
    data = {
        "id": res.id,
        "name": res.name,
        "remark": res.remark,
    }
    return success_response(message="新建项目成功", data=data)


@router.post("/member")
async def assign_member(
    body: ProjectMemberRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="仅经理可分配成员")
    member, project, user = await add_project_member(
        db, body.user_id, body.project_id
    )
    await delete_cached_project_list(body.user_id)
    return success_response(
        message="分配成功",
        data={
            "id": member.id,
            "user_id": member.user_id,
            "project_id": member.project_id,
            "project_name": project.name,
            "username": user.username,
        },
    )


@router.get("/alluser")
async def get_curproject_user(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = await get_all_user(db, project_id)
    data = []
    for member, user in rows:
        data.append(
            {
                "user_id": member.user_id,
                "username": user.username,
                "employee_no": user.employee_no,
            }
        )
    return success_response(message="返回此项目全部用户成功", data=data)


@router.delete("/member")
async def delete_member(
    body: ProjectMemberRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="仅经理可移除成员")
    await remove_project_member(db, body.user_id, body.project_id)
    await delete_cached_project_list(body.user_id)
    return success_response(
        message="移除成功",
        data={"user_id": body.user_id, "project_id": body.project_id},
    )


@router.get("/gap_status_count")
async def get_count(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cached = await get_cached_gap_count(project_id)
    if cached is not None:
        return success_response(message="获取差距项状态成功", data=cached)

    row = await get_gapscount(project_id, db)
    await set_cached_gap_count(project_id, row)
    return success_response(message="获取差距项状态成功", data=row)


@router.post("/gap/create")
async def create_gap(
    body: GapCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = await create_gaps(
        db,
        body.project_id,
        body.title,
        current_user.id,
        current_user.role,
        category=body.category,
        risk_level=body.risk_level,
        reason=body.reason,
        requirement=body.requirement,
    )
    await delete_cached_gap_count(body.project_id)
    return success_response(
        message="录入差距成功",
        data={
            "id": row.id,
            "project_id": row.project_id,
            "title": row.title,
            "status": row.status,
            "category": row.category,
            "risk_level": row.risk_level,
            "reason": row.reason,
            "requirement": row.requirement,
            "create_at": row.create_at,
        },
    )
