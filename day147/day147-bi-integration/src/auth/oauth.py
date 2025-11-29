from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from config.settings import settings
from src.models import TokenData

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="oauth/token")

# Mock user database - replace with real auth in production
# WARNING: These are development credentials only. Change all passwords in production!
# Passwords are hashed before storage, but these defaults should not be used in production.
# Initialize passwords lazily to avoid bcrypt initialization issues
_USERS_DB_RAW = {
    "tableau": {
        "username": "tableau",
        "password": "tableau_secret",  # CHANGE IN PRODUCTION
        "scopes": ["read:metrics", "read:exports"],
        "allowed_services": ["api", "web", "database"]
    },
    "powerbi": {
        "username": "powerbi",
        "password": "powerbi_secret",  # CHANGE IN PRODUCTION
        "scopes": ["read:metrics"],
        "allowed_services": ["api", "web"]
    },
    "admin": {
        "username": "admin",
        "password": "admin_secret",  # CHANGE IN PRODUCTION
        "scopes": ["read:metrics", "write:exports", "admin"],
        "allowed_services": ["*"]
    }
}

_USERS_DB = None

def _init_users_db():
    """Initialize users database with hashed passwords"""
    global _USERS_DB
    if _USERS_DB is None:
        _USERS_DB = {}
        for username, user_data in _USERS_DB_RAW.items():
            _USERS_DB[username] = {
                "username": user_data["username"],
                "hashed_password": pwd_context.hash(user_data["password"]),
                "scopes": user_data["scopes"],
                "allowed_services": user_data["allowed_services"]
            }
    return _USERS_DB

def get_users_db():
    """Get users database, initializing if needed"""
    return _init_users_db()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str):
    users_db = get_users_db()
    if username in users_db:
        return users_db[username]
    return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        scopes: List[str] = payload.get("scopes", [])
        allowed_services: List[str] = payload.get("allowed_services", [])
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, scopes=scopes, allowed_services=allowed_services)
    except JWTError:
        raise credentials_exception
    return token_data

def check_permission(user: TokenData, required_scope: str):
    if required_scope not in user.scopes and "admin" not in user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

def filter_by_allowed_services(user: TokenData, services: List[str]) -> List[str]:
    if "*" in user.allowed_services:
        return services
    return [s for s in services if s in user.allowed_services]
