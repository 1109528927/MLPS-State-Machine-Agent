from datetime import datetime
from turtle import update
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, false, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import UniqueConstraint  # 文件顶部和其他 import 放一起

class Base(DeclarativeBase):
    create_at: Mapped[datetime] = mapped_column(
        DateTime,
        insert_default=func.now(),
        default=func.now,
        comment="这是创建时间",
    )


class Test(Base):
    __tablename__ = "chat_records"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_input: Mapped[str] = mapped_column(Text)
    agent_output: Mapped[str] = mapped_column(Text)


class User(Base):
    __tablename__ = "user"
    id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    username:Mapped[str]=mapped_column(String(50),unique=True,nullable=False)
    password:Mapped[str]=mapped_column(String(255),nullable=False)
    employee_no:Mapped[str]=mapped_column(String(50),unique=True,nullable=False)
    role:Mapped[str]=mapped_column(String(20),nullable=False,default="inspector")
    updated_at:Mapped[datetime]=mapped_column(DateTime,  insert_default=func.now(),
        default=func.now,onupdate=func.now())


class UserToken(Base):
    __tablename__ = "user_token"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

class Project(Base):
    __tablename__ = "project"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # created_at 若在基类里已有就不用再写；基类没有就在这里补一列，名字和库一致

class GapItem(Base):
    __tablename__ = "gap_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="待整改")
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirement: Mapped[str | None] = mapped_column(Text, nullable=True)
    # create_at 继承自 Base，就不用再写

class GapActionLog(Base):
    __tablename__ = "gap_action_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gap_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("gap_item.id"), nullable=False
    )
    actor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    from_status: Mapped[str] = mapped_column(String(20), nullable=False)
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    # create_at 继承 Base

   
class ProjectMember(Base):
    __tablename__ = "project_member"
    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="uk_user_project"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project.id"), nullable=False
    )
    # create_at 继承自 Base，表里若有这一列就和库对齐；没有可先不加列