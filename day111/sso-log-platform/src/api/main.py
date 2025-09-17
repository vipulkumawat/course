"""Main FastAPI application for SSO-enabled log platform"""
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, HTTPException, Depends, Cookie, Response
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sso.gateway import sso_gateway, AuthToken

app = FastAPI(title="SSO Log Platform", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Authentication middleware for protected routes"""
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response

def get_current_user(request: Request, session_token: Optional[str] = Cookie(None)) -> Optional[Dict[str, Any]]:
    """Get current authenticated user from session"""
    if not session_token:
        return None
    
    try:
        user_data = sso_gateway.validate_jwt_token(session_token)
        return user_data
    except Exception:
        return None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """Home page - redirect to login if not authenticated"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "page_title": "Log Platform Dashboard"
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """Login page with SSO provider options"""
    if current_user:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "page_title": "Login - Log Platform"
    })

@app.get("/success", response_class=HTMLResponse)
async def success_page(request: Request, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """Success page shown after successful authentication"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("success.html", {
        "request": request,
        "user": current_user,
        "page_title": "Authentication Successful - SSO Log Platform"
    })

@app.get("/auth/{provider}")
async def initiate_auth(provider: str, request: Request):
    """Initiate SSO authentication flow"""
    if provider not in ["google", "okta"]:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    
    # Demo mode - simulate successful authentication
    if sso_gateway.config.environment == "development":
        return RedirectResponse(url=f"/auth/{provider}/demo", status_code=302)
    
    # Generate state parameter for CSRF protection
    state = str(uuid.uuid4())
    sso_gateway.redis_client.setex(f"auth_state:{state}", 600, provider)  # 10 minutes
    
    if provider == "google":
        auth_url = sso_gateway.get_google_auth_url(state)
    elif provider == "okta":
        auth_url = sso_gateway.get_okta_auth_url(state)
    
    return RedirectResponse(url=auth_url, status_code=302)

@app.get("/auth/{provider}/demo")
async def demo_auth(provider: str, request: Request):
    """Demo authentication - simulates successful OAuth flow"""
    if provider not in ["google", "okta"]:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    
    # Create demo user data
    demo_user_info = {
        "email": f"demo.user@{provider}.com",
        "name": f"Demo {provider.title()} User",
        "provider": provider,
        "id": f"demo_{provider}_12345"
    }
    
    # Determine tenant
    tenant_id = sso_gateway.determine_tenant_from_email(demo_user_info["email"])
    
    # Generate JWT token
    jwt_token = sso_gateway.generate_jwt_token(demo_user_info, tenant_id)
    
    # Create response with secure cookie
    response = RedirectResponse(url="/success", status_code=302)
    response.set_cookie(
        key="session_token",
        value=jwt_token,
        max_age=86400,  # 24 hours
        httponly=True,
        secure=True,
        samesite="lax"
    )
    
    return response

@app.get("/auth/google/callback")
async def google_callback(request: Request, code: str, state: str):
    """Handle Google OAuth callback"""
    # Verify state parameter
    stored_provider = sso_gateway.redis_client.get(f"auth_state:{state}")
    if not stored_provider or stored_provider != "google":
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    sso_gateway.redis_client.delete(f"auth_state:{state}")
    
    try:
        # Exchange code for user info
        user_info = await sso_gateway.exchange_google_code(code)
        
        # Determine tenant
        tenant_id = sso_gateway.determine_tenant_from_email(user_info["email"])
        
        # Generate JWT token
        jwt_token = sso_gateway.generate_jwt_token(user_info, tenant_id)
        
        # Create response with secure cookie
        response = RedirectResponse(url="/success", status_code=302)
        response.set_cookie(
            key="session_token",
            value=jwt_token,
            max_age=86400,  # 24 hours
            httponly=True,
            secure=True,
            samesite="lax"
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@app.get("/auth/okta/callback")
async def okta_callback(request: Request, code: str, state: str):
    """Handle Okta OAuth callback"""
    # Verify state parameter
    stored_provider = sso_gateway.redis_client.get(f"auth_state:{state}")
    if not stored_provider or stored_provider != "okta":
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    sso_gateway.redis_client.delete(f"auth_state:{state}")
    
    try:
        # Exchange code for user info
        user_info = await sso_gateway.exchange_okta_code(code)
        
        # Determine tenant
        tenant_id = sso_gateway.determine_tenant_from_email(user_info["email"])
        
        # Generate JWT token
        jwt_token = sso_gateway.generate_jwt_token(user_info, tenant_id)
        
        # Create response with secure cookie
        response = RedirectResponse(url="/success", status_code=302)
        response.set_cookie(
            key="session_token",
            value=jwt_token,
            max_age=86400,  # 24 hours
            httponly=True,
            secure=True,
            samesite="lax"
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@app.post("/logout")
async def logout():
    """Logout user and clear session"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="session_token")
    return response

@app.get("/api/user")
async def get_user_info(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """Get current user information"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "email": current_user["email"],
        "name": current_user["name"],
        "tenant_id": current_user["tenant_id"],
        "provider": current_user["provider"],
        "authenticated_at": current_user["iat"]
    }

@app.get("/api/logs")
async def get_logs(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """Get logs for authenticated user's tenant"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Simulate tenant-specific logs
    sample_logs = [
        {
            "timestamp": "2025-05-20T10:30:00Z",
            "level": "INFO",
            "service": "auth-service",
            "message": f"User {current_user['email']} authenticated",
            "tenant_id": current_user["tenant_id"]
        },
        {
            "timestamp": "2025-05-20T10:29:45Z",
            "level": "DEBUG",
            "service": "log-processor",
            "message": "Processing log batch",
            "tenant_id": current_user["tenant_id"]
        },
        {
            "timestamp": "2025-05-20T10:29:30Z",
            "level": "WARN",
            "service": "data-ingestion",
            "message": "High memory usage detected",
            "tenant_id": current_user["tenant_id"]
        }
    ]
    
    return {
        "logs": sample_logs,
        "tenant_id": current_user["tenant_id"],
        "total_count": len(sample_logs)
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
