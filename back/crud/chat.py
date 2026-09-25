
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from model.chat import Test

async def get_rencent_info(db:AsyncSession,skip:int=0,limit:int=20):
    stmt=select(Test).offset(skip).limit(limit).order_by(Test.create_at.desc())
    result=await db.execute(stmt)
    result_orm=result.scalars().all()
    return result_orm


async def post_inset_info(db: AsyncSession,user_input: str,last_reply:str):
    row = Test(
    user_input=user_input,      # 前端传给路由传来的 body.user_input
    agent_output=last_reply,  # agent 返回的 last_reply
)
    db.add(row)           # 加入会话（还没真正落库 / 还没有自增 id）
    await db.commit()      # 提交到数据库
    await db.refresh(row) # 刷新对象：把库里生成的 id、默认值等读回来
    return row            # 返回这条新对象，给路由用（后面生成 token 要用 user.id）