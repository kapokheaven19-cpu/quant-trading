"""
OpenAPI 平台 - 应用管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, App
from app.schemas import (
    AppCreate, AppUpdate, AppResponse, AppDetailResponse, 
    AppSecretResetResponse, MessageResponse, PaginatedResponse
)
from app.security import hash_password, generate_app_id, generate_app_secret, verify_app_secret
from app.api.user import get_current_user

router = APIRouter(prefix="/api/apps", tags=["应用管理"])


@router.post("", response_model=AppDetailResponse, status_code=status.HTTP_201_CREATED)
def create_app(
    app_data: AppCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建应用"""
    # 生成 AppID 和 AppSecret
    app_id = generate_app_id()
    app_secret, app_secret_hash = generate_app_secret()
    
    # 创建应用
    app = App(
        name=app_data.name,
        app_id=app_id,
        app_secret_hash=app_secret_hash,
        description=app_data.description,
        user_id=current_user.id
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    
    # 返回包含 AppSecret（仅创建时可见）
    return AppDetailResponse(
        id=app.id,
        name=app.name,
        app_id=app.app_id,
        app_secret=app_secret,  # 仅此时返回明文
        description=app.description,
        is_active=app.is_active,
        created_at=app.created_at
    )


@router.get("", response_model=PaginatedResponse)
def list_apps(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取应用列表"""
    query = db.query(App).filter(App.user_id == current_user.id)
    total = query.count()
    apps = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        items=[AppResponse.model_validate(app) for app in apps],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{app_id}", response_model=AppResponse)
def get_app(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取应用详情"""
    app = db.query(App).filter(
        App.id == app_id,
        App.user_id == current_user.id
    ).first()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="应用不存在"
        )
    
    return AppResponse.model_validate(app)


@router.put("/{app_id}", response_model=AppResponse)
def update_app(
    app_id: int,
    app_data: AppUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新应用"""
    app = db.query(App).filter(
        App.id == app_id,
        App.user_id == current_user.id
    ).first()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="应用不存在"
        )
    
    if app_data.name:
        app.name = app_data.name
    if app_data.description is not None:
        app.description = app_data.description
    
    db.commit()
    db.refresh(app)
    
    return AppResponse.model_validate(app)


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_app(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除应用"""
    app = db.query(App).filter(
        App.id == app_id,
        App.user_id == current_user.id
    ).first()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="应用不存在"
        )
    
    db.delete(app)
    db.commit()
    
    return None


@router.post("/{app_id}/reset-secret", response_model=AppSecretResetResponse)
def reset_app_secret(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重置应用密钥"""
    app = db.query(App).filter(
        App.id == app_id,
        App.user_id == current_user.id
    ).first()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="应用不存在"
        )
    
    # 生成新的 AppSecret
    app_secret, app_secret_hash = generate_app_secret()
    app.app_secret_hash = app_secret_hash
    db.commit()
    
    return AppSecretResetResponse(app_id=app.app_id, app_secret=app_secret)
