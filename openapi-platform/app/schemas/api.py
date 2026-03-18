from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# User schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


# Token schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None


# API Key schemas
class APIKeyCreate(BaseModel):
    name: Optional[str] = None
    scopes: List[str] = []
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    id: int
    app_id: str
    name: Optional[str]
    scopes: List[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class APIKeyWithSecret(APIKeyResponse):
    app_secret: str


# OAuth schemas
class OAuthAppCreate(BaseModel):
    name: str
    redirect_uris: List[str] = []
    grant_types: List[str] = ["authorization_code"]
    scopes: List[str] = ["read"]


class OAuthAppResponse(BaseModel):
    id: int
    client_id: str
    name: str
    redirect_uris: List[str]
    grant_types: List[str]
    scopes: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class OAuthAppWithSecret(OAuthAppResponse):
    client_secret: str


class OAuthAuthorize(BaseModel):
    client_id: str
    redirect_uri: str
    response_type: str = "code"
    scope: str = "read"
    state: Optional[str] = None


class OAuthToken(BaseModel):
    grant_type: str
    code: Optional[str] = None
    refresh_token: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: Optional[str] = None


# Managed API schemas
class ManagedAPICreate(BaseModel):
    path: str
    method: str
    target_url: str
    auth_required: bool = True
    is_public: bool = False
    description: Optional[str] = None


class ManagedAPIResponse(BaseModel):
    id: int
    path: str
    method: str
    target_url: str
    auth_required: bool
    is_public: bool
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Access Log schemas
class AccessLogResponse(BaseModel):
    id: int
    api_id: Optional[int]
    method: str
    path: str
    status_code: int
    response_time: Optional[int]
    ip_address: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
