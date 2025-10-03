# auth.py
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from database import users_collection  # MongoDB collection

# Charger les variables d'environnement
load_dotenv()

# Configuration JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "180"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

print("ACCESS_TOKEN_EXPIRE_MINUTES =", ACCESS_TOKEN_EXPIRE_MINUTES)

import bcrypt

# Security scheme
security = HTTPBearer()

# ===============================
# Gestion des mots de passe
# ===============================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # Convert strings to bytes
        pwd_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        # Verify the password
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception as e:
        print(f"Password verification error: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    # Convert password to bytes and generate salt
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    # Hash the password and convert back to string
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

# ===============================
# Gestion des tokens JWT
# ===============================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_refresh_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload.get("sub")
    except JWTError:
        return None

def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

# ===============================
# Authentification
# ===============================
async def authenticate_user(email: str, password: str) -> Optional[dict]:
    user = await users_collection.find_one({"email": email})
    if not user:
        print(f"Authentication failed: No user found with email {email}")
        return None
    if not verify_password(password, user["password"]):
        print(f"Authentication failed: Invalid password for user {email}")
        return None
    if not user.get("is_active", True):
        print(f"Authentication failed: User {email} is not active")
        return None
    print(f"Authentication successful for user {email}")
    return user

# ===============================
# Current user
# ===============================
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    token = credentials.credentials
    email = verify_token(token)
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    return user

# ===============================
# Permissions
# ===============================
def require_role(allowed_roles: list):
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of these roles: {allowed_roles}"
            )
        return current_user
    return role_checker

# Helpers
require_admin = require_role(["admin"])
require_teacher_or_admin = require_role(["teacher", "admin"])
require_student_or_higher = require_role(["student", "teacher", "admin"])
