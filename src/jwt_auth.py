"""
JWT (JSON Web Token) Authentication Module

This module provides JWT token creation, verification, and user authentication
using cryptographic signing with HS256 algorithm.

Usage:
    from jwt_auth import create_token, verify_token, authenticate_user
    
    # Create token
    token = create_token({"user_id": 1, "username": "john"})
    
    # Verify token
    payload = verify_token(token)
"""

import jwt
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from pydantic import BaseModel
from passlib.context import CryptContext
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """Token payload model."""
    user_id: int
    username: str
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None


class User(BaseModel):
    """User model for authentication."""
    user_id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True


class UserInDB(User):
    """User model with hashed password."""
    hashed_password: str


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
    
    Returns:
        True if passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> Token:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary with token payload (must include 'user_id' and 'username')
        expires_delta: Custom expiration time (default: 30 minutes)
    
    Returns:
        Token object with access_token, token_type, and expires_in
    
    Example:
        ```python
        token = create_token({
            "user_id": 1,
            "username": "john_doe"
        })
        ```
    """
    try:
        # Validate required fields
        if "user_id" not in data or "username" not in data:
            raise ValueError("Token payload must include 'user_id' and 'username'")
        
        # Copy data to avoid mutation
        to_encode = data.copy()
        
        # Set expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Add expiration and issued at timestamps
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow()
        })
        
        # Encode JWT token
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        logger.info(f"Token created for user: {data.get('username')}")
        
        # Calculate expires_in in seconds
        expires_in = int((expire - datetime.utcnow()).total_seconds())
        
        return Token(
            access_token=encoded_jwt,
            token_type="bearer",
            expires_in=expires_in
        )
    
    except Exception as e:
        logger.error(f"Error creating token: {str(e)}")
        raise


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload or None if verification fails
    
    Raises:
        jwt.ExpiredSignatureError: Token has expired
        jwt.InvalidTokenError: Token is invalid
    
    Example:
        ```python
        payload = verify_token(token)
        if payload:
            user_id = payload.get("user_id")
        ```
    """
    try:
        # Decode and verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        logger.info(f"Token verified for user: {payload.get('username')}")
        return payload
    
    except jwt.ExpiredSignatureError:
        logger.warning(f"Expired token")
        raise
    
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise
    
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        return None


def decode_token_unsafe(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode token without verification (unsafe, use only for inspection).
    
    WARNING: This function does NOT verify the token signature.
    Use only for debugging or inspection purposes.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload or None if decoding fails
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        logger.warning("Token decoded without verification (unsafe)")
        return payload
    
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        return None


def authenticate_user(
    username: str,
    password: str,
    users_db: Dict[str, UserInDB]
) -> Optional[User]:
    """
    Authenticate a user by username and password.
    
    Args:
        username: Username
        password: Plain text password
        users_db: Dictionary of users from database
    
    Returns:
        User object if authentication succeeds, None otherwise
    
    Example:
        ```python
        users = {
            "john": UserInDB(
                user_id=1,
                username="john",
                hashed_password=hash_password("secret123")
            )
        }
        user = authenticate_user("john", "secret123", users)
        ```
    """
    if username not in users_db:
        logger.warning(f"User not found: {username}")
        return None
    
    user = users_db[username]
    
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Invalid password for user: {username}")
        return None
    
    if not user.is_active:
        logger.warning(f"Inactive user attempted login: {username}")
        return None
    
    logger.info(f"User authenticated: {username}")
    return User(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active
    )


def is_token_expired(token: str) -> bool:
    """
    Check if a token is expired without raising exceptions.
    
    Args:
        token: JWT token string
    
    Returns:
        True if token is expired, False otherwise
    """
    try:
        payload = decode_token_unsafe(token)
        if payload and "exp" in payload:
            exp_time = datetime.fromtimestamp(payload["exp"])
            return exp_time < datetime.utcnow()
        return False
    except Exception as e:
        logger.error(f"Error checking token expiration: {str(e)}")
        return True


def get_token_expiration_time(token: str) -> Optional[datetime]:
    """
    Get the expiration time of a token.
    
    Args:
        token: JWT token string
    
    Returns:
        Expiration datetime or None if unable to determine
    """
    try:
        payload = decode_token_unsafe(token)
        if payload and "exp" in payload:
            return datetime.fromtimestamp(payload["exp"])
        return None
    except Exception as e:
        logger.error(f"Error getting token expiration: {str(e)}")
        return None


def get_token_age_seconds(token: str) -> Optional[int]:
    """
    Get the age of a token in seconds since it was issued.
    
    Args:
        token: JWT token string
    
    Returns:
        Age in seconds or None if unable to determine
    """
    try:
        payload = decode_token_unsafe(token)
        if payload and "iat" in payload:
            issued_time = datetime.fromtimestamp(payload["iat"])
            age = datetime.utcnow() - issued_time
            return int(age.total_seconds())
        return None
    except Exception as e:
        logger.error(f"Error getting token age: {str(e)}")
        return None
