"""
OpenAPI 平台 - API 路由初始化
"""
from fastapi import APIRouter
from app.api import user, app, openapi, oauth, gateway

# 创建主路由
api_router = APIRouter()

# 用户认证路由
api_router.include_router(user.router)

# 用户管理路由
api_router.include_router(user.user_router)

# 应用管理路由
api_router.include_router(app.router)

# 接口管理路由
api_router.include_router(openapi.router)

# OAuth2.0 路由
api_router.include_router(oauth.router)

# 开放接口（网关）
api_router.include_router(gateway.router)
