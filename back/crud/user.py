from datetime import datetime,timedelta
from sqlalchemy import select
from sqlalchemy.engine import row
from sqlalchemy.ext.asyncio import AsyncSession
from model.chat import User,UserToken
from passlib.context import CryptContext

import uuid
async def post_userinfo(db:AsyncSession,username,pwd):
    stmt=select(User).where(User.username==username)
    result=await db.execute(stmt)
    result_orm=result.scalar_one_or_none()
    return result_orm
pwd_obj=CryptContext(schemes=["bcrypt"],deprecated="auto")
async def add_user(db: AsyncSession, username: str, password: str, employee_no: str):
    row = User(
        username=username,
        password=pwd_obj.hash(password),
        employee_no=employee_no,
        role="inspector",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


#这个函数目的是注册获取token，供路由通过token进行判断的，因为只把 token **写进数据库还不够**——前端拿不到token，后面请求就**没法带证**。
async def post_token(db:AsyncSession,user_id):
    token=str(uuid.uuid4())
    expires_at = datetime.now()+timedelta(days=7)
    stmt=select(UserToken).where(UserToken.user_id==user_id)
    result=await db.execute(stmt)
    result_orm=result.scalar_one_or_none()
    if result_orm:
        result_orm.token=token
        result_orm.expires_at=expires_at
    else:
         row = UserToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
         db.add(row)
    await db.commit()
    return token     

async def post_login(db: AsyncSession, username, password):
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    result_orm = result.scalar_one_or_none()
    if not result_orm:
        return None
    if not pwd_obj.verify(password, result_orm.password):
        return None
    return result_orm


async def get_user_by_token(db: AsyncSession, token: str):
    stmt = select(UserToken).where(UserToken.token == token)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if not row:
        return None
    if row.expires_at < datetime.now():
        return None
    stmt_user = select(User).where(User.id == row.user_id)
    return (await db.execute(stmt_user)).scalar_one_or_none()

