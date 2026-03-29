from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
import secrets
import string
import urllib.parse

from app.db.database import get_db
from app.models.user import User, OAuthApp
from app.schemas.api import OAuthAppCreate, OAuthAppResponse, OAuthAppWithSecret, OAuthAuthorize, OAuthToken
from app.api.routes.auth import get_current_user
from app.core.security import create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/oauth", tags=["OAuth2.0"])

# In-memory storage for authorization codes (use Redis in production)
authorization_codes = {}


def generate_client_id():
    return ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(32))


def generate_client_secret():
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(48))


@router.get("/apps", response_model=List[OAuthAppResponse])
def list_oauth_apps(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    apps = db.query(OAuthApp).filter(OAuthApp.user_id == current_user.id).all()
    return apps


@router.post("/apps", response_model=OAuthAppWithSecret)
def create_oauth_app(
    app_data: OAuthAppCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    client_id = generate_client_id()
    client_secret = generate_client_secret()
    
    db_app = OAuthApp(
        user_id=current_user.id,
        client_id=client_id,
        client_secret=client_secret,
        name=app_data.name,
        redirect_uris=app_data.redirect_uris,
        grant_types=app_data.grant_types,
        scopes=app_data.scopes
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    
    return OAuthAppWithSecret(
        id=db_app.id,
        client_id=db_app.client_id,
        client_secret=client_secret,
        name=db_app.name,
        redirect_uris=db_app.redirect_uris,
        grant_types=db_app.grant_types,
        scopes=db_app.scopes,
        created_at=db_app.created_at
    )


@router.delete("/apps/{app_id}")
def delete_oauth_app(
    app_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    app = db.query(OAuthApp).filter(
        OAuthApp.id == app_id,
        OAuthApp.user_id == current_user.id
    ).first()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OAuth app not found"
        )
    
    db.delete(app)
    db.commit()
    return {"message": "OAuth app deleted"}


@router.get("/authorize")
def authorize(
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    response_type: str = Query("code"),
    scope: str = Query("read"),
    state: str = Query(None),
    db: Session = Depends(get_db)
):
    # Validate client
    app = db.query(OAuthApp).filter(OAuthApp.client_id == client_id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client_id"
        )
    
    if redirect_uri not in app.redirect_uris:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect_uri"
        )
    
    # Generate authorization code
    code = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    authorization_codes[code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state
    }
    
    # Redirect to authorization confirmation (simplified - normally would show a UI)
    params = urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code": code,
        "state": state or ""
    })
    
    return HTMLResponse(content=f"""
    <html>
    <head><title>Authorization</title></head>
    <body>
        <h2>Authorize Application?</h2>
        <p>Application: {app.name}</p>
        <p>Scope: {scope}</p>
        <form method="post" action="/api/oauth/confirm">
            <input type="hidden" name="code" value="{code}">
            <button type="submit">Authorize</button>
        </form>
    </body>
    </html>
    """)


@router.post("/confirm")
def confirm_authorization(
    code: str,
    db: Session = Depends(get_db)
):
    code_data = authorization_codes.pop(code, None)
    if not code_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired authorization code"
        )
    
    params = urllib.parse.urlencode({
        "code": code,
        "state": code_data.get("state", "")
    })
    
    return HTMLResponse(
        content=f"""
        <html>
        <head><script>
            window.opener.postMessage({{type: 'oauth', code: '{code}'}}, '*');
            window.close();
        </script></head>
        <body>Authorized! Closing...</body>
        </html>
        """,
        headers={"Location": f"{code_data['redirect_uri']}?{params}"}
    )


@router.post("/token", response_model=dict)
def token(
    grant_type: str = Query(...),
    code: str = Query(None),
    refresh_token: str = Query(None),
    client_id: str = Query(None),
    client_secret: str = Query(None),
    redirect_uri: str = Query(None),
    db: Session = Depends(get_db)
):
    if grant_type == "authorization_code":
        if not code or not client_id or not redirect_uri:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required parameters"
            )
        
        code_data = authorization_codes.pop(code, None)
        if not code_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired authorization code"
            )
        
        app = db.query(OAuthApp).filter(
            OAuthApp.client_id == client_id,
            OAuthApp.client_secret == client_secret
        ).first()
        
        if not app:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client credentials"
            )
        
        # Generate tokens (simplified - normally would create a user session)
        access_token = create_access_token(data={"sub": str(app.user_id), "client_id": client_id})
        refresh_token_token = create_refresh_token(data={"sub": str(app.user_id), "client_id": client_id})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token_token,
            "token_type": "Bearer",
            "expires_in": 1800
        }
    
    elif grant_type == "refresh_token":
        if not refresh_token or not client_id or not client_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required parameters"
            )
        
        payload = decode_token(refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid refresh token"
            )
        
        app = db.query(OAuthApp).filter(
            OAuthApp.client_id == client_id,
            OAuthApp.client_secret == client_secret
        ).first()
        
        if not app:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client credentials"
            )
        
        access_token = create_access_token(data={"sub": str(app.user_id), "client_id": client_id})
        
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 1800
        }
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported grant type"
        )
