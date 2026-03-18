from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    api_keys = relationship("APIKey", back_populates="user")
    oauth_apps = relationship("OAuthApp", back_populates="user")
    managed_apis = relationship("ManagedAPI", back_populates="user")


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    app_id = Column(String(100), unique=True, index=True, nullable=False)
    app_secret = Column(String(255), nullable=False)
    name = Column(String(255))
    scopes = Column(JSON, default=list)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="api_keys")


class OAuthApp(Base):
    __tablename__ = "oauth_apps"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(String(100), unique=True, index=True, nullable=False)
    client_secret = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    redirect_uris = Column(JSON, default=list)
    grant_types = Column(JSON, default=["authorization_code"])
    scopes = Column(JSON, default=["read"])
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="oauth_apps")


class ManagedAPI(Base):
    __tablename__ = "managed_apis"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    path = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    target_url = Column(String(500), nullable=False)
    auth_required = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="managed_apis")


class AccessLog(Base):
    __tablename__ = "access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, ForeignKey("managed_apis.id"), nullable=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    method = Column(String(10))
    path = Column(String(255))
    status_code = Column(Integer)
    request_headers = Column(JSON)
    request_body = Column(Text)
    response_body = Column(Text)
    response_time = Column(Integer)
    ip_address = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
