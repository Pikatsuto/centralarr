from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Optional
import secrets
import requests
import os

from backend.database import get_db
from backend.models import User, Group, SSOProvider

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Password hashing utils
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Constants for JWT
SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[int] = None):
    from datetime import datetime, timedelta
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta or ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

async def authenticate_user(db: Session, username: str, password: str):
    user = await get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

# Dependency to get current user
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await get_user(db, username=username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    # Add checks like is_active if needed
    return current_user

async def admin_required(current_user: User = Depends(get_current_active_user)):
    admin_group = next((g for g in current_user.groups if g.name == "admin"), None)
    if not admin_group:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

# LOGIN LOCAL - token generation
@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# USER INFO
@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        # Add groups, permissions if needed
    }

# REGISTER (admin only)
@router.post("/register")
async def register_user(user_data: dict, current_user: User = Depends(admin_required), db: Session = Depends(get_db)):
    username = user_data.get("username")
    email = user_data.get("email")
    password = user_data.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    user_exist = await db.query(User).filter(User.username == username).first()
    if user_exist:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = hash_password(password)
    new_user = User(username=username, email=email, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created", "id": new_user.id}

# LOGOUT - JWT strategy doesn’t require server logout but can be implemented with token blacklist if needed

# --- SSO ROUTES (OAuth/OpenID Connect) ---
from fastapi.responses import RedirectResponse

@router.get("/login_sso/{provider_name}")
async def login_sso(provider_name: str, request: Request, db: Session = Depends(get_db)):
    provider = db.query(SSOProvider).filter(SSOProvider.name == provider_name, SSOProvider.enabled == True).first()
    if not provider:
        raise HTTPException(status_code=404, detail="SSO Provider not found")

    # Generate state and save in session (requires session middleware or alternative)
    state = secrets.token_urlsafe(16)
    # Here you need to save state in a place accessible to verify later (session, redis...)
    # For this example, skipping implementing session storage, but must be done in production

    redirect_uri = request.url_for("auth.sso_callback", provider_name=provider_name)
    params = {
        "response_type": "code",
        "client_id": provider.client_id,
        "redirect_uri": redirect_uri,
        "scope": provider.scope,
        "state": state
    }
    from urllib.parse import urlencode
    redirect_url = f"{provider.auth_url}?{urlencode(params)}"
    return RedirectResponse(redirect_url)

@router.get("/sso/callback/{provider_name}")
async def sso_callback(provider_name: str, request: Request, db: Session = Depends(get_db)):
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    # Here verify state that was saved earlier

    provider = db.query(SSOProvider).filter(SSOProvider.name == provider_name, SSOProvider.enabled == True).first()
    if not provider:
        raise HTTPException(status_code=404, detail="SSO Provider not found")

    token_response = requests.post(
        provider.token_url,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": str(request.url_for("auth.sso_callback", provider_name=provider_name)),
            "client_id": provider.client_id,
            "client_secret": provider.client_secret,
        },
    )

    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get token from provider")

    tokens = token_response.json()
    access_token = tokens.get("access_token")

    userinfo_response = requests.get(provider.userinfo_url, headers={"Authorization": f"Bearer {access_token}"})
    if userinfo_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch user info")

    userinfo = userinfo_response.json()

    email = userinfo.get("email")
    username = userinfo.get("preferred_username") or userinfo.get("email")

    # lookup user or create
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(username=username, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    # Create JWT token for user (or alternatively set session cookie)
    access_token = create_access_token({"sub": user.username})

    # return token or redirect with cookie
    # Here a redirect to frontend with token in query param or cookie is common
    return {"access_token": access_token, "token_type": "bearer"}