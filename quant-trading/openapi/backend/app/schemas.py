"""
OpenAPI 平台 - Pydantic 数据模型（请求/响应）
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ========== 用户相关 ==========
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)


# ========== 应用相关 ==========
class AppCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class AppUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class AppResponse(BaseModel):
    id: int
    name: str
    app_id: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AppDetailResponse(AppResponse):
    """创建应用时返回，包含 AppSecret（仅此时可见）"""
    app_secret: Optional[str] = None


class AppSecretResetResponse(BaseModel):
    app_id: str
    app_secret: str


# ========== 接口相关 ==========
class ApiParam(BaseModel):
    name: str
    type: str
    required: bool
    description: Optional[str] = None


class ApiBody(BaseModel):
    content_type: str = "application/json"
    body_schema: Optional[Dict[str, Any]] = Field(None, alias="schema")


class ApiResponse(BaseModel):
    content_type: str = "application/json"
    response_schema: Optional[Dict[str, Any]] = Field(None, alias="schema")
    example: Optional[Dict[str, Any]] = None


class ApiCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    path: str = Field(..., pattern=r"^/[\w\-/]*$")
    method: str = Field(..., pattern=r"^(GET|POST|PUT|DELETE|PATCH)$")
    description: Optional[str] = None
    request_params: Optional[List[ApiParam]] = None
    request_body: Optional[ApiBody] = None
    response_body: Optional[ApiResponse] = None
    backend_url: str


class ApiUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    request_params: Optional[List[ApiParam]] = None
    request_body: Optional[ApiBody] = None
    response_body: Optional[ApiResponse] = None
    backend_url: Optional[str] = None


class ApiResponseModel(BaseModel):
    id: int
    name: str
    path: str
    method: str
    description: Optional[str]
    request_params: Optional[List[Dict[str, Any]]]
    request_body: Optional[Dict[str, Any]]
    response_body: Optional[Dict[str, Any]]
    backend_url: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== 权限管理相关 ==========
class ApiAccessCreate(BaseModel):
    app_id: int


class ApiAccessResponse(BaseModel):
    id: int
    api_id: int
    app_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ApiAccessWithApp(BaseModel):
    id: int
    api_id: int
    app: AppResponse
    created_at: datetime


# ========== OAuth2.0 相关 ==========
class OAuthAuthorizeRequest(BaseModel):
    client_id: str
    redirect_uri: str
    response_type: str = "code"
    scope: Optional[str] = None
    state: Optional[str] = None


class OAuthTokenRequest(BaseModel):
    grant_type: str  # authorization_code, client_credentials, refresh_token
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None


class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


# ========== JWT 相关 ==========
class JWTPayload(BaseModel):
    sub: str  # user_id:app_id
    exp: datetime
    iat: Optional[datetime] = None


# ========== 通用响应 ==========
class MessageResponse(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
