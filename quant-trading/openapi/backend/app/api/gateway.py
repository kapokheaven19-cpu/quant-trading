"""
OpenAPI 平台 - 接口网关（处理实际接口调用）
"""
import time
import httpx
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import App, Api, ApiAccess, ApiLog, User
from app.security import (
    verify_app_secret, decode_access_token, verify_api_key_signature,
    generate_jwt_token
)

router = APIRouter(prefix="/openapi", tags=["开放接口"])


def get_client_ip(request: Request) -> str:
    """获取客户端 IP"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def openapi_gateway(
    path: str,
    request: Request,
    app_id: str = Query(None),
    app_secret: str = Query(None),
    token: str = Query(None),
    db: Session = Depends(get_db)
):
    """开放API网关入口 - 支持多种认证方式"""
    
    start_time = time.time()
    client_ip = get_client_ip(request)
    method = request.method
    
    # 获取请求参数
    query_params = dict(request.query_params)
    # 移除认证相关参数
    auth_params = {}
    if app_id:
        auth_params["app_id"] = app_id
    if app_secret:
        auth_params["app_secret"] = app_secret
    if token:
        auth_params["token"] = token
    
    for key in ["app_id", "app_secret", "token", "sign", "timestamp"]:
        query_params.pop(key, None)
    
    # 获取请求体
    request_body = None
    try:
        request_body = await request.body()
        if request_body:
            request_body = request_body.decode("utf-8")
    except:
        pass
    
    # 认证方式 1: API 密钥认证
    authenticated_app = None
    auth_type = None
    
    if app_id and app_secret:
        # API 密钥认证
        auth_type = "api_key"
        app = db.query(App).filter(App.app_id == app_id, App.is_active == True).first()
        if not app:
            await log_request(db, None, None, method, f"/{path}", query_params, request_body, 
                            401, None, "无效的 AppID", client_ip, request.headers.get("user-agent"), start_time)
            raise HTTPException(status_code=401, detail="无效的 AppID")
        
        if not verify_app_secret(app_secret, app.app_secret_hash):
            await log_request(db, app.id, None, method, f"/{path}", query_params, request_body,
                            401, None, "AppSecret 验证失败", client_ip, request.headers.get("user-agent"), start_time)
            raise HTTPException(status_code=401, detail="AppSecret 验证失败")
        
        authenticated_app = app
    
    # 认证方式 2: JWT Token 认证
    elif token:
        auth_type = "jwt"
        payload = decode_access_token(token)
        if not payload:
            await log_request(db, None, None, method, f"/{path}", query_params, request_body,
                            401, None, "无效的 Token", client_ip, request.headers.get("user-agent"), start_time)
            raise HTTPException(status_code=401, detail="无效的 Token")
        
        # 获取 app_id
        app_id_from_token = payload.get("app_id")
        if app_id_from_token:
            app = db.query(App).filter(App.id == int(app_id_from_token), App.is_active == True).first()
            if app:
                authenticated_app = app
        
        # 如果没有关联应用，尝试通过 user_id 查找
        if not authenticated_app:
            user_id = payload.get("sub")
            if user_id:
                # 查找用户的第一个活跃应用
                app = db.query(App).filter(App.user_id == int(user_id), App.is_active == True).first()
                if app:
                    authenticated_app = app
    
    # 认证方式 3: OAuth2.0 Bearer Token
    else:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            auth_type = "bearer"
            bearer_token = auth_header[7:]
            payload = decode_access_token(bearer_token)
            
            if not payload:
                await log_request(db, None, None, method, f"/{path}", query_params, request_body,
                                401, None, "无效的 Bearer Token", client_ip, request.headers.get("user-agent"), start_time)
                raise HTTPException(status_code=401, detail="无效的 Token")
            
            app_id_from_token = payload.get("app_id")
            if app_id_from_token:
                app = db.query(App).filter(App.id == int(app_id_from_token), App.is_active == True).first()
                if app:
                    authenticated_app = app
    
    if not authenticated_app:
        await log_request(db, None, None, method, f"/{path}", query_params, request_body,
                        401, None, "未提供认证信息", client_ip, request.headers.get("user-agent"), start_time)
        raise HTTPException(status_code=401, detail="认证失败")
    
    # 查找对应的接口定义
    api = db.query(Api).filter(
        Api.path == f"/{path}",
        Api.method == method,
        Api.status == "published"
    ).first()
    
    if not api:
        await log_request(db, authenticated_app.id, None, method, f"/{path}", query_params, request_body,
                        404, None, "接口不存在或未发布", client_ip, request.headers.get("user-agent"), start_time)
        raise HTTPException(status_code=404, detail="接口不存在或未发布")
    
    # 检查接口访问权限
    has_access = db.query(ApiAccess).filter(
        ApiAccess.api_id == api.id,
        ApiAccess.app_id == authenticated_app.id
    ).first() is not None
    
    # 允许接口创建者访问自己的接口
    if not has_access and api.user_id == authenticated_app.user_id:
        has_access = True
    
    if not has_access:
        await log_request(db, authenticated_app.id, api.id, method, f"/{path}", query_params, request_body,
                        403, None, "无接口访问权限", client_ip, request.headers.get("user-agent"), start_time)
        raise HTTPException(status_code=403, detail="无接口访问权限")
    
    # 转发请求到实际后端服务
    try:
        backend_url = api.backend_url.rstrip("/")
        full_url = f"{backend_url}/{path}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                resp = await client.get(full_url, params=query_params)
            elif method == "POST":
                resp = await client.post(full_url, params=query_params, content=request_body)
            elif method == "PUT":
                resp = await client.put(full_url, params=query_params, content=request_body)
            elif method == "DELETE":
                resp = await client.delete(full_url, params=query_params)
            elif method == "PATCH":
                resp = await client.patch(full_url, params=query_params, content=request_body)
            else:
                raise HTTPException(status_code=405, detail="不支持的 HTTP 方法")
        
        response_status = resp.status_code
        response_body = resp.text
        
    except httpx.RequestError as e:
        await log_request(db, authenticated_app.id, api.id, method, f"/{path}", query_params, request_body,
                        502, None, f"后端服务调用失败: {str(e)}", client_ip, request.headers.get("user-agent"), start_time)
        raise HTTPException(status_code=502, detail="后端服务不可用")
    
    # 记录日志
    await log_request(db, authenticated_app.id, api.id, method, f"/{path}", query_params, request_body,
                    response_status, response_body, None, client_ip, request.headers.get("user-agent"), start_time)
    
    # 返回响应
    return {
        "code": response_status,
        "data": response_body,
        "message": "success" if response_status < 400 else "error"
    }


async def log_request(
    db: Session,
    app_id: int,
    api_id: int,
    method: str,
    path: str,
    query_params: dict,
    request_body: str,
    response_status: int,
    response_body: str,
    error_message: str,
    ip_address: str,
    user_agent: str,
    start_time: float
):
    """记录接口调用日志"""
    latency_ms = int((time.time() - start_time) * 1000)
    
    log = ApiLog(
        api_id=api_id or 0,
        app_id=app_id,
        method=method,
        path=path,
        query_params=str(query_params) if query_params else None,
        request_body=request_body,
        response_status=response_status,
        response_body=response_body[:2000] if response_body else None,  # 限制长度
        error_message=error_message,
        ip_address=ip_address,
        user_agent=user_agent,
        latency_ms=latency_ms
    )
    db.add(log)
    db.commit()


# JWT 令牌发放接口（简化版）
@router.post("/token")
async def generate_jwt(
    app_id: str = Query(...),
    app_secret: str = Query(...),
    db: Session = Depends(get_db)
):
    """生成 JWT Token（简化版，用于接口调用）"""
    app = db.query(App).filter(App.app_id == app_id, App.is_active == True).first()
    if not app:
        raise HTTPException(status_code=401, detail="无效的 AppID")
    
    if not verify_app_secret(app_secret, app.app_secret_hash):
        raise HTTPException(status_code=401, detail="AppSecret 验证失败")
    
    jwt_token = generate_jwt_token(app.user_id, str(app.id))
    
    return {
        "access_token": jwt_token,
        "token_type": "Bearer",
        "expires_in": 7200  # 2小时
    }
