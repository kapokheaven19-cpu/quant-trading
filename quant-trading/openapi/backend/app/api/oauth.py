"""
OpenAPI 平台 - OAuth2.0 认证 API
"""
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, App, AccessToken, Api
from app.schemas import OAuthTokenRequest, OAuthTokenResponse
from app.security import hash_password, verify_app_secret, create_access_token, decode_access_token
from app.api.user import get_current_user

router = APIRouter(prefix="/oauth", tags=["OAuth2.0认证"])

# OAuth2.0 配置
OAUTH_CODE_EXPIRE_MINUTES = 10
ACCESS_TOKEN_EXPIRE_HOURS = 2
REFRESH_TOKEN_EXPIRE_DAYS = 30

# 内存存储授权码（生产环境应使用 Redis）
oauth_codes = {}  # {code: {"client_id": xxx, "redirect_uri": xxx, "user_id": xxx, "expires_at": xxx}}


@router.get("/authorize", response_class=HTMLResponse)
def oauth_authorize(
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    response_type: str = Query("code"),
    scope: str = Query(None),
    state: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """OAuth2.0 授权页面"""
    # 验证 client_id
    app = db.query(App).filter(App.app_id == client_id, App.user_id == current_user.id).first()
    if not app:
        return HTMLResponse(content="无效的 client_id", status_code=400)
    
    # 返回授权确认页面 HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>授权确认</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; }}
            .container {{ border: 1px solid #ddd; padding: 30px; border-radius: 8px; }}
            h2 {{ color: #333; }}
            .app-name {{ font-weight: bold; color: #1890ff; }}
            .buttons {{ margin-top: 20px; }}
            button {{ padding: 10px 20px; margin-right: 10px; border: none; border-radius: 4px; cursor: pointer; }}
            .allow {{ background: #1890ff; color: white; }}
            .deny {{ background: #ddd; color: #333; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>授权确认</h2>
            <p>应用 <span class="app-name">{app.name}</span> 请求访问您的账户</p>
            <p>这将允许该应用：</p>
            <ul>
                <li>通过 API 访问您的接口</li>
                <li>获取接口调用权限</li>
            </ul>
            <form method="post" action="/oauth/authorize">
                <input type="hidden" name="client_id" value="{client_id}">
                <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                <input type="hidden" name="scope" value="{scope or ''}">
                <input type="hidden" name="state" value="{state or ''}">
                <div class="buttons">
                    <button type="submit" name="action" value="allow" class="allow">授权</button>
                    <button type="submit" name="action" value="deny" class="deny">拒绝</button>
                </div>
            </form>
        </div>
    </body>
    </html>
    """
    return html


@router.post("/authorize", response_class=HTMLResponse)
def oauth_authorize_submit(
    client_id: str,
    redirect_uri: str,
    scope: str = None,
    state: str = None,
    action: str = "deny",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """处理 OAuth2.0 授权提交"""
    if action == "deny":
        # 用户拒绝，重定向回 redirect_uri 并带错误
        return HTMLResponse(
            content=f"<script>window.location.href='{redirect_uri}?error=access_denied&state={state or ''}'</script>"
        )
    
    # 用户授权，生成授权码
    app = db.query(App).filter(App.app_id == client_id, App.user_id == current_user.id).first()
    if not app:
        return HTMLResponse(content="无效的 client_id", status_code=400)
    
    code = secrets.token_urlsafe(32)
    oauth_codes[code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "user_id": current_user.id,
        "expires_at": datetime.utcnow() + timedelta(minutes=OAUTH_CODE_EXPIRE_MINUTES)
    }
    
    # 重定向回应用
    from urllib.parse import urlencode
    params = {"code": code}
    if state:
        params["state"] = state
    
    return HTMLResponse(
        content=f"<script>window.location.href='{redirect_uri}?{urlencode(params)}'</script>"
    )


@router.post("/token", response_model=OAuthTokenResponse)
def oauth_token(
    token_data: OAuthTokenRequest,
    db: Session = Depends(get_db)
):
    """获取访问令牌"""
    
    if token_data.grant_type == "authorization_code":
        # 授权码模式
        if not token_data.code:
            raise HTTPException(status_code=400, detail="缺少授权码")
        
        code_data = oauth_codes.get(token_data.code)
        if not code_data:
            raise HTTPException(status_code=400, detail="无效的授权码")
        
        if datetime.utcnow() > code_data["expires_at"]:
            del oauth_codes[token_data.code]
            raise HTTPException(status_code=400, detail="授权码已过期")
        
        # 验证 client_id 和 redirect_uri
        if code_data["client_id"] != token_data.client_id:
            raise HTTPException(status_code=400, detail="client_id 不匹配")
        
        # 获取应用
        app = db.query(App).filter(App.app_id == token_data.client_id).first()
        if not app:
            raise HTTPException(status_code=400, detail="无效的 client_id")
        
        # 验证 client_secret
        if not verify_app_secret(token_data.client_secret or "", app.app_secret_hash):
            raise HTTPException(status_code=400, detail="client_secret 错误")
        
        # 生成令牌
        access_token = create_access_token(
            data={"sub": str(code_data["user_id"]), "app_id": str(app.id), "type": "access"},
            expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        )
        refresh_token = secrets.token_urlsafe(32)
        
        # 存储刷新令牌
        refresh_token_record = AccessToken(
            token=refresh_token,
            token_type="bearer",
            expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            app_id=app.id,
            user_id=code_data["user_id"],
            scope=code_data.get("scope")
        )
        db.add(refresh_token_record)
        
        # 删除已使用的授权码
        del oauth_codes[token_data.code]
        db.commit()
        
        return OAuthTokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            refresh_token=refresh_token,
            scope=code_data.get("scope")
        )
    
    elif token_data.grant_type == "client_credentials":
        # 客户端模式
        if not token_data.client_id or not token_data.client_secret:
            raise HTTPException(status_code=400, detail="缺少 client_id 或 client_secret")
        
        app = db.query(App).filter(App.app_id == token_data.client_id).first()
        if not app:
            raise HTTPException(status_code=400, detail="无效的 client_id")
        
        if not verify_app_secret(token_data.client_secret, app.app_secret_hash):
            raise HTTPException(status_code=400, detail="client_secret 错误")
        
        # 生成令牌
        access_token = create_access_token(
            data={"sub": str(app.user_id), "app_id": str(app.id), "type": "client"},
            expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        )
        
        return OAuthTokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600
        )
    
    elif token_data.grant_type == "refresh_token":
        # 刷新令牌
        if not token_data.refresh_token:
            raise HTTPException(status_code=400, detail="缺少 refresh_token")
        
        token_record = db.query(AccessToken).filter(
            AccessToken.token == token_data.refresh_token,
            AccessToken.token_type == "bearer"
        ).first()
        
        if not token_record:
            raise HTTPException(status_code=400, detail="无效的 refresh_token")
        
        if datetime.utcnow() > token_record.expires_at:
            raise HTTPException(status_code=400, detail="refresh_token 已过期")
        
        # 生成新令牌
        access_token = create_access_token(
            data={"sub": str(token_record.user_id), "app_id": str(token_record.app_id), "type": "access"},
            expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        )
        
        return OAuthTokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600
        )
    
    else:
        raise HTTPException(status_code=400, detail="不支持的 grant_type")


@router.post("/revoke")
def oauth_revoke(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """撤销令牌"""
    token_record = db.query(AccessToken).filter(AccessToken.token == token).first()
    if token_record:
        db.delete(token_record)
        db.commit()
    
    return {"message": "令牌已撤销"}


@router.get("/jwks")
def oauth_jwks():
    """返回 JWKS（JSON Web Key Set）"""
    # 简化实现，实际应使用非对称加密
    return {
        "keys": [
            {
                "kty": "oct",
                "k": "openapi-platform-secret-key",
                "alg": "HS256",
                "use": "sig"
            }
        ]
    }
