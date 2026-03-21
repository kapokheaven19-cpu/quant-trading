"""
OpenAPI 平台 - 数据库模型定义
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    apps = relationship("App", back_populates="user", cascade="all, delete-orphan")
    apis = relationship("Api", back_populates="user", cascade="all, delete-orphan")


class App(Base):
    __tablename__ = "apps"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    app_id = Column(String(32), unique=True, nullable=False)
    app_secret_hash = Column(String(255), nullable=False)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="apps")
    api_access = relationship("ApiAccess", back_populates="app", cascade="all, delete-orphan")
    tokens = relationship("AccessToken", back_populates="app", cascade="all, delete-orphan")


class Api(Base):
    __tablename__ = "apis"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    path = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    description = Column(Text)
    request_params = Column(JSON)
    request_body = Column(JSON)
    response_body = Column(JSON)
    backend_url = Column(String(255), nullable=False)
    status = Column(String(20), default="draft")  # draft, published, deprecated
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="apis")
    access = relationship("ApiAccess", back_populates="api", cascade="all, delete-orphan")
    logs = relationship("ApiLog", back_populates="api", cascade="all, delete-orphan")


class ApiAccess(Base):
    __tablename__ = "api_access"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    api_id = Column(Integer, ForeignKey("apis.id", ondelete="CASCADE"), nullable=False)
    app_id = Column(Integer, ForeignKey("apps.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint("api_id", "app_id", name="uq_api_app"),)
    
    api = relationship("Api", back_populates="access")
    app = relationship("App", back_populates="api_access")


class AccessToken(Base):
    __tablename__ = "access_tokens"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(255), unique=True, nullable=False)
    token_type = Column(String(20), nullable=False)  # bearer, jwt
    expires_at = Column(DateTime, nullable=False)
    app_id = Column(Integer, ForeignKey("apps.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    scope = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    app = relationship("App", back_populates="tokens")


class ApiLog(Base):
    __tablename__ = "api_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    api_id = Column(Integer, ForeignKey("apis.id", ondelete="CASCADE"), nullable=False)
    app_id = Column(Integer, ForeignKey("apps.id", ondelete="SET NULL"), nullable=True)
    method = Column(String(10), nullable=False)
    path = Column(String(255), nullable=False)
    query_params = Column(Text)
    request_body = Column(Text)
    response_status = Column(Integer)
    response_body = Column(Text)
    error_message = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    latency_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    api = relationship("Api", back_populates="logs")
