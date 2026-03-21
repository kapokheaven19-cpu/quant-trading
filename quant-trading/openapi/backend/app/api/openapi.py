"""
OpenAPI 平台 - 接口管理 API
"""
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict

from app.database import get_db
from app.models import User, Api, App, ApiAccess
from app.schemas import (
    ApiCreate, ApiUpdate, ApiResponseModel, ApiAccessCreate,
    ApiAccessResponse, AppResponse, MessageResponse, PaginatedResponse
)
from app.api.user import get_current_user

router = APIRouter(prefix="/api/openapis", tags=["接口管理"])


@router.post("", response_model=ApiResponseModel, status_code=status.HTTP_201_CREATED)
def create_api(
    api_data: ApiCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建接口定义"""
    # 检查路径和方法是否已存在（同一用户下）
    existing = db.query(Api).filter(
        Api.path == api_data.path,
        Api.method == api_data.method,
        Api.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该接口路径和方法已存在"
        )
    
    # 转换 Pydantic 模型为字典
    api = Api(
        name=api_data.name,
        path=api_data.path,
        method=api_data.method,
        description=api_data.description,
        request_params=[p.model_dump() for p in api_data.request_params] if api_data.request_params else None,
        request_body=api_data.request_body.model_dump() if api_data.request_body else None,
        response_body=api_data.response_body.model_dump() if api_data.response_body else None,
        backend_url=api_data.backend_url,
        status="draft",
        user_id=current_user.id
    )
    db.add(api)
    db.commit()
    db.refresh(api)
    
    return api


@router.get("", response_model=PaginatedResponse)
def list_apis(
    page: int = 1,
    page_size: int = 10,
    status: str = None,
    keyword: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取接口列表"""
    query = db.query(Api).filter(Api.user_id == current_user.id)
    
    if status:
        query = query.filter(Api.status == status)
    if keyword:
        query = query.filter(Api.name.contains(keyword) | Api.path.contains(keyword))
    
    total = query.count()
    apis = query.order_by(Api.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        items=[ApiResponseModel.model_validate(api) for api in apis],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{api_id}", response_model=ApiResponseModel)
def get_api(
    api_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取接口详情"""
    api = db.query(Api).filter(
        Api.id == api_id,
        Api.user_id == current_user.id
    ).first()
    
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口不存在"
        )
    
    return ApiResponseModel.model_validate(api)


@router.put("/{api_id}", response_model=ApiResponseModel)
def update_api(
    api_id: int,
    api_data: ApiUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新接口定义"""
    api = db.query(Api).filter(
        Api.id == api_id,
        Api.user_id == current_user.id
    ).first()
    
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口不存在"
        )
    
    if api_data.name is not None:
        api.name = api_data.name
    if api_data.description is not None:
        api.description = api_data.description
    if api_data.request_params is not None:
        api.request_params = [p.model_dump() if hasattr(p, 'model_dump') else p for p in api_data.request_params]
    if api_data.request_body is not None:
        api.request_body = api_data.request_body.model_dump() if hasattr(api_data.request_body, 'model_dump') else api_data.request_body
    if api_data.response_body is not None:
        api.response_body = api_data.response_body.model_dump() if hasattr(api_data.response_body, 'model_dump') else api_data.response_body
    if api_data.backend_url is not None:
        api.backend_url = api_data.backend_url
    
    db.commit()
    db.refresh(api)
    
    return ApiResponseModel.model_validate(api)


@router.delete("/{api_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api(
    api_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除接口"""
    api = db.query(Api).filter(
        Api.id == api_id,
        Api.user_id == current_user.id
    ).first()
    
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口不存在"
        )
    
    db.delete(api)
    db.commit()
    
    return None


@router.post("/{api_id}/publish", response_model=MessageResponse)
def publish_api(
    api_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发布接口"""
    api = db.query(Api).filter(
        Api.id == api_id,
        Api.user_id == current_user.id
    ).first()
    
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口不存在"
        )
    
    if api.status == "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="接口已发布"
        )
    
    api.status = "published"
    db.commit()
    
    return {"message": "接口发布成功"}


@router.post("/{api_id}/unpublish", response_model=MessageResponse)
def unpublish_api(
    api_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """下架接口"""
    api = db.query(Api).filter(
        Api.id == api_id,
        Api.user_id == current_user.id
    ).first()
    
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口不存在"
        )
    
    if api.status != "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="接口未发布"
        )
    
    api.status = "draft"
    db.commit()
    
    return {"message": "接口下架成功"}


# ========== 权限管理 ==========
@router.post("/{api_id}/access", response_model=ApiAccessResponse, status_code=status.HTTP_201_CREATED)
def grant_api_access(
    api_id: int,
    access_data: ApiAccessCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """授权应用访问接口"""
    # 检查接口是否存在
    api = db.query(Api).filter(
        Api.id == api_id,
        Api.user_id == current_user.id
    ).first()
    
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口不存在"
        )
    
    # 检查应用是否存在且属于当前用户
    app = db.query(App).filter(
        App.id == access_data.app_id,
        App.user_id == current_user.id
    ).first()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="应用不存在"
        )
    
    # 检查是否已授权
    existing = db.query(ApiAccess).filter(
        ApiAccess.api_id == api_id,
        ApiAccess.app_id == access_data.app_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该应用已有访问权限"
        )
    
    # 创建授权
    access = ApiAccess(api_id=api_id, app_id=access_data.app_id)
    db.add(access)
    db.commit()
    db.refresh(access)
    
    return access


@router.get("/{api_id}/access", response_model=List[ApiAccessResponse])
def list_api_access(
    api_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取接口授权列表"""
    # 检查接口是否存在
    api = db.query(Api).filter(
        Api.id == api_id,
        Api.user_id == current_user.id
    ).first()
    
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口不存在"
        )
    
    accesses = db.query(ApiAccess).filter(ApiAccess.api_id == api_id).all()
    return accesses


@router.delete("/{api_id}/access/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_access(
    api_id: int,
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消接口授权"""
    # 检查接口是否存在
    api = db.query(Api).filter(
        Api.id == api_id,
        Api.user_id == current_user.id
    ).first()
    
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口不存在"
        )
    
    # 查找授权记录
    access = db.query(ApiAccess).filter(
        ApiAccess.api_id == api_id,
        ApiAccess.app_id == app_id
    ).first()
    
    if not access:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="授权记录不存在"
        )
    
    db.delete(access)
    db.commit()
    
    return None


# ========== 接口测试 ==========
@router.post("/{api_id}/test", response_model=Dict)
def test_api(
    api_id: int,
    test_data: Dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """测试接口 - 直接调用后端服务"""
    import httpx
    import time
    
    # 检查接口是否存在
    api = db.query(Api).filter(
        Api.id == api_id,
        Api.user_id == current_user.id
    ).first()
    
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口不存在"
        )
    
    if api.status != "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有已发布的接口才能测试"
        )
    
    # 提取测试参数
    method = test_data.get("method", api.method)
    query_params = test_data.get("query_params", {})
    request_body = test_data.get("body", None)
    headers = test_data.get("headers", {})
    
    start_time = time.time()
    
    try:
        backend_url = api.backend_url.rstrip("/")
        # 使用 api.path 作为完整路径
        api_path = api.path.lstrip("/") if api.path else ""
        full_url = f"{backend_url}/{api_path}"
        
        # 移除认证相关的 headers
        headers = {k: v for k, v in headers.items() if k.lower() not in ["authorization", "x-app-id", "x-app-secret"]}
        
        # 构建查询参数
        url_params = {}
        for k, v in query_params.items():
            if v:
                url_params[k] = str(v)
        
        with httpx.Client(timeout=30.0, follow_redirects=True, proxy=None) as client:
            req_kwargs = {"params": url_params}
            
            if request_body:
                # 尝试解析 JSON
                try:
                    req_kwargs["json"] = json.loads(request_body)
                    req_kwargs["headers"] = {"Content-Type": "application/json", **headers}
                except:
                    req_kwargs["content"] = request_body
                    req_kwargs["headers"] = {"Content-Type": "text/plain", **headers}
            else:
                req_kwargs["headers"] = headers
            
            if method == "GET":
                resp = client.get(full_url, **req_kwargs)
            elif method == "POST":
                resp = client.post(full_url, **req_kwargs)
            elif method == "PUT":
                resp = client.put(full_url, **req_kwargs)
            elif method == "DELETE":
                resp = client.delete(full_url, **req_kwargs)
            elif method == "PATCH":
                resp = client.patch(full_url, **req_kwargs)
            else:
                raise HTTPException(status_code=405, detail="不支持的 HTTP 方法")
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # 尝试解析 JSON 响应
        try:
            response_data = resp.json()
        except:
            response_data = resp.text
        
        return {
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": response_data,
            "latency_ms": latency_ms,
            "debug_url": full_url  # 调试信息
        }
        
    except httpx.RequestError as e:
        return {
            "status_code": 502,
            "error": f"后端服务调用失败: {str(e)}",
            "debug_url": full_url,
            "latency_ms": int((time.time() - start_time) * 1000)
        }
    except Exception as e:
        return {
            "status_code": 500,
            "error": f"测试失败: {str(e)}",
            "debug_url": full_url,
            "latency_ms": int((time.time() - start_time) * 1000)
        }
