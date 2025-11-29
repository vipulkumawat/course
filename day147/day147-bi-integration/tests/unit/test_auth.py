import pytest
from src.auth.oauth import verify_password, create_access_token, authenticate_user
from datetime import timedelta

def test_password_verification():
    """Test password hashing and verification"""
    from src.auth.oauth import pwd_context
    password = "test_password"
    hashed = pwd_context.hash(password)
    
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)

def test_token_creation():
    """Test JWT token creation"""
    data = {"sub": "testuser", "scopes": ["read:metrics"]}
    token = create_access_token(data, expires_delta=timedelta(minutes=30))
    
    assert isinstance(token, str)
    assert len(token) > 0

def test_user_authentication():
    """Test user authentication"""
    # Valid credentials
    user = authenticate_user("tableau", "tableau_secret")
    assert user is not False
    assert user["username"] == "tableau"
    
    # Invalid credentials
    user = authenticate_user("tableau", "wrong_password")
    assert user is False
