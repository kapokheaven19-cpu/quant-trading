"""
OpenAPI 平台 - 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.api import api_router

# 初始化数据库
init_db()

# 创建 FastAPI 应用
app = FastAPI(
    title="OpenAPI 开放平台",
    description="统一的接口托管与服务出口平台",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(api_router)


@app.get("/")
def root():
    """根路径"""
    return {
        "message": "欢迎使用 OpenAPI 开放平台",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
