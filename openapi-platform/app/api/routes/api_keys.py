from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import secrets
import string

from app.db.database import get_db
from app.models.user import User, APIKey
from app.schemas.api import APIKeyCreate, APIKeyResponse, APIKeyWithSecret
from app.api.routes.auth import get_current_user

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


def generate_app_id():
    return ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(32))


def generate_app_secret():
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(48))


@router.get("", response_model=List[APIKeyResponse])
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    return api_keys


@router.post("", response_model=APIKeyWithSecret)
def create_api_key(
    api_key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    app_id = generate_app_id()
    app_secret = generate_app_secret()
    
    db_api_key = APIKey(
        user_id=current_user.id,
        app_id=app_id,
        app_secret=app_secret,
        name=api_key_data.name,
        scopes=api_key_data.scopes,
        expires_at=api_key_data.expires_at
    )
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    
    # Include secret in response only on creation
    result = APIKeyWithSecret(
        id=db_api_key.id,
        app_id=db_api_key.app_id,
        app_secret=app_secret,
        name=db_api_key.name,
        scopes=db_api_key.scopes,
        is_active=db_api_key.is_active,
        created_at=db_api_key.created_at
    )
    return result


@router.delete("/{api_key_id}")
def delete_api_key(
    api_key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    api_key = db.query(APIKey).filter(
        APIKey.id == api_key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    db.delete(api_key)
    db.commit()
    return {"message": "API key deleted"}


@router.post("/{api_key_id}/toggle")
def toggle_api_key(
    api_key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    api_key = db.query(APIKey).filter(
        APIKey.id == api_key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    api_key.is_active = not api_key.is_active
    db.commit()
    return {"is_active": api_key.is_active}
