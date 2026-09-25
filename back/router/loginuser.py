from config.request import get_db
from fastapi import APIRouter, Depends,HTTPException
from schema.loginuser import UserRequest,loginRequest
from sqlalchemy.ext.asyncio import AsyncSession
from crud.user import post_token, post_userinfo,add_user,post_login
from utils.response import success_response
from utils.auth import get_current_user
from model.chat import User
from cache.auth_cache import set_cached_user_id
router = APIRouter(prefix="/api/user", tags=["login"])




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

    return success_response(message="登录成功",data=data)


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