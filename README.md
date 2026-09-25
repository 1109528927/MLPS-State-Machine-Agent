# 等保整改跟踪工作台

Vue3 + FastAPI + MySQL + Redis + LangChain Agent。

## 

做了一个**等保整改跟踪工作台**：登录后按**项目**管理**差距项**，用**状态机**推进整改并写**操作日志**。经理可开通账号、建项目、分配成员；核查员只能看到自己被分配的项目。另有**智能助手**：用自然语言查询项目列表、差距状态统计等。

| 层 | 技术 | 作用 |
|----|------|------|
| 前端 | Vue3、Vue Router、Element Plus、Axios | 工作台、差距抽屉、开通账号、聊天 |
| 后端 | FastAPI、SQLAlchemy、Pydantic | 业务 API、鉴权、统一响应 |
| 数据 | MySQL | 用户 / 项目 / 成员 / 差距 / 日志 / 聊天记录 |
| 缓存 | Redis | Token、项目列表、差距状态统计（旁路缓存） |
| 智能 | LangChain Agent + Tools | 查业务库问答；短期记忆；结构化输出 |

**想强调的三点：**

1. **业务闭环：** 选项目 → 推状态 → 留痕迹；角色 + 成员表控制数据范围；状态用转移表驱动，后端校验才是安全边界。  
2. **工程习惯：** Bearer Token 鉴权、路由守卫 + 401 拦截、开通账号前后端校验对齐。  
3. **选型说得清：** Redis 旁路读、写后删；Agent 用 Tool 查结构化库，不上 RAG（问的是库表数据，不是文档）。

**演示路径：**

```text
经理登录 → 项目列表 → 差距页改状态 / 看统计
       → 智能助手：「我有哪些项目」「某项目待整改几条」
核查员登录 → 仅可见自己的项目
```

---

## 功能一览

- 登录 / 退出；经理开通账号  
- 项目列表（可搜索）；新建项目；分配 / 移除成员  
- 差距项列表、录入、状态流转与操作历史  
- 单项目差距状态统计  
- 智能助手（工具查库 + 多轮短期记忆）  
- Redis：token / 项目列表 / 状态统计缓存  

---

## 架构示意

```text
浏览器 (Vue)
  → Vite 代理 /api
  → FastAPI
       ├─ 鉴权 get_current_user（可走 Redis token）
       ├─ 项目 / 差距 / 成员 CRUD（MySQL）
       ├─ 列表与统计旁路缓存（Redis）
       └─ Agent：Tools 查库 → 回答（可选结构化）
```

---

## 目录结构

```text
min_agent_app_review/
├── back/                 # FastAPI
│   ├── router/           # 登录、项目、聊天
│   ├── crud/             # 数据访问
│   ├── cache/            # Redis 策略
│   ├── agent/            # LangChain Agent
│   ├── Dockerfile
│   └── config/           # DB、Redis（支持环境变量）
├── front/front_mini_agent/   # Vue3 + Nginx 镜像
├── docker/mysql/init.sql     # 首次建表 + 种子账号
├── docker-compose.yml
├── .env.example
├── README.md
├── 等保实施.md            # 个人实施学习笔记（可不对外）
└── 缓存点.md
```

---

## Docker 一键启动（推荐演示）

本机若提示 `docker` 找不到或连不上 daemon：先打开 **Docker Desktop**，在 Settings → Resources → WSL integration 里勾选你的 Linux 发行版，再开新终端。

```bash
# 1. 项目根目录准备 .env（含百炼 Key）
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY 等

# 2. 构建并启动：MySQL + Redis + 后端 + 前端
docker compose up -d --build

# 3. 浏览器打开前端
# http://localhost:8080
# API 文档（可选）：http://localhost:8000/docs
```

**种子账号（仅空数据卷首次 init 时写入）：**

| 用户名 | 密码 | 角色 |
|--------|------|------|
| `manager` | `123456` | 经理 |
| `inspector` | `123456` | 核查员（已分配 a 项目） |

常用命令：

```bash
docker compose ps
docker compose logs -f backend
docker compose down          # 停容器，保留数据卷
docker compose down -v       # 停并清空 MySQL/Redis 数据（慎用）
```

容器内连接：后端通过服务名 `mysql` / `redis` 访问（环境变量 `DATABASE_URL`、`REDIS_HOST`），不必改业务代码里的默认 localhost（本地开发仍可用）。

---

## 本地运行（不容器）

**依赖：** MySQL、Redis、Python 3.12+（建议 uv）、Node.js、百炼 API Key。

```bash
# 后端（在 back/）
# DATABASE_URL / REDIS_HOST 默认指向 localhost
# uv pip install -r requirement.txt --python .venv
# cd back && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 前端（在 front/front_mini_agent/）
pnpm install
pnpm dev
```

敏感信息放根目录 `.env`，不要提交仓库。

---

## 说明

仓库内 `等保实施.md` / `缓存点.md` 为**个人学习与复习笔记**，不必对外分发；对外以本 README 为准。


