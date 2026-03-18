from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from typing import List
import httpx
import time

from app.db.database import get_db
from app.models.user import User, ManagedAPI, APIKey
from app.schemas.api import ManagedAPICreate, ManagedAPIResponse, AccessLogResponse
from app.api.routes.auth import get_current_user

router = APIRouter(prefix="/managed-apis", tags=["Managed APIs"])


@router.get("", response_model=List[ManagedAPIResponse])
def list_managed_apis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    apis = db.query(ManagedAPI).filter(ManagedAPI.user_id == current_user.id).all()
    return apis


@router.post("", response_model=ManagedAPIResponse)
def create_managed_api(
    api_data: ManagedAPICreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_api = ManagedAPI(
        user_id=current_user.id,
        path=api_data.path,
        method=api_data.method.upper(),
        target_url=api_data.target_url,
        auth_required=api_data.auth_required,
        is_public=api_data.is_public,
        description=api_data.description
    )
    db.add(db_api)
    db.commit()
    db.refresh(db_api)
    return db_api


@router.put("/{api_id}", response_model=ManagedAPIResponse)
def update_managed_api(
    api_id: int,
    api_data: ManagedAPICreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_api = db.query(ManagedAPI).filter(
        ManagedAPI.id == api_id,
        ManagedAPI.user_id == current_user.id
    ).first()
    
    if not db_api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API not found"
        )
    
    db_api.path = api_data.path
    db_api.method = api_data.method.upper()
    db_api.target_url = api_data.target_url
    db_api.auth_required = api_data.auth_required
    db_api.is_public = api_data.is_public
    db_api.description = api_data.description
    
    db.commit()
    db.refresh(db_api)
    return db_api


@router.delete("/{api_id}")
def delete_managed_api(
    api_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_api = db.query(ManagedAPI).filter(
        ManagedAPI.id == api_id,
        ManagedAPI.user_id == current_user.id
    ).first()
    
    if not db_api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API not found"
        )
    
    db.delete(db_api)
    db.commit()
    return {"message": "API deleted"}


# Gateway router for proxying requests
gateway_router = APIRouter(prefix="/gateway", tags=["Gateway"])


def extract_api_key(request: Request):
    """Extract API key from request headers"""
    app_id = request.headers.get("X-App-ID")
    app_secret = request.headers.get("X-App-Secret")
    return app_id, app_secret


def extract_jwt_token(request: Request):
    """Extract JWT token from Authorization header"""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


@gateway_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway_proxy(
    path: str,
    request: Request,
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    # Find matching managed API
    method = request.method
    db_api = db.query(ManagedAPI).filter(
        ManagedAPI.path == f"/{path}",
        ManagedAPI.method == method
    ).first()
    
    if not db_api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API not found"
        )
    
    # Check authentication
    api_key = None
    jwt_token = None
    
    if not db_api.is_public:
        app_id, app_secret = extract_api_key(request)
        
        if app_id and app_secret:
            api_key = db.query(APIKey).filter(
                APIKey.app_id == app_id,
                APIKey.app_secret == app_secret,
                APIKey.is_active == True
            ).first()
            
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API credentials"
                )
        else:
            # Try JWT
            jwt_token = extract_jwt_token(request)
            if not jwt_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
    
    # Forward request to target
    target_url = f"{db_api.target_url.rstrip('/')}/{path}"
    
    headers = dict(request.headers)
    headers.pop("host", None)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=target_url,
                headers=headers,
                content=await request.body(),
                params=request.query_params
            )
            
        response_time = int((time.time() - start_time) * 1000)
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to proxy request: {str(e)}"
        )
