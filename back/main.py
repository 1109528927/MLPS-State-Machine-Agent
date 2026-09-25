from fastapi import FastAPI
from router import chat, loginuser,project
from fastapi.middleware.cors import CORSMiddleware
from utils.exception import register_exception_handlers
app=FastAPI()
register_exception_handlers(app)
@app.get("/")
async def root():
    return {"message": "Hello World"}

app.add_middleware(CORSMiddleware,
    allow_origins=["*"],     # 允许访问的源
    allow_credentials=True,  # 允许携带 Cookie
    allow_methods=["*"],    # 允许所有请求方法
    allow_headers=["*"]
)

app.include_router(chat.router)
app.include_router(loginuser.router)
app.include_router(project.router)