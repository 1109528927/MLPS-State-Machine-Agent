import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from router import chat, loginuser, project
from utils.exception import register_exception_handlers

logger = logging.getLogger(__name__)


async def _boot_warmup() -> None:
    """进程启动时预热模型客户端，缩短首登后第一次对话。"""
    try:
        from agent.agent import warmup_agent

        await asyncio.to_thread(warmup_agent)
        logger.info("boot warmup done")
    except Exception as exc:  # noqa: BLE001
        logger.warning("boot warmup failed: %s", exc)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    asyncio.create_task(_boot_warmup())
    yield


app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(loginuser.router)
app.include_router(project.router)
