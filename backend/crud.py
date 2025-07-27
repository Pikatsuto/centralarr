from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models import User, Group, Permission, ProxyService, SSOProvider
from backend.auth import get_current_active_user  # On suppose qu’elle gère la récupération user
from backend.auth import admin_required  # Dépendance pour protéger routes aux admins

router = APIRouter(prefix="/api/crud", tags=["crud"])

# --- USERS ---

@router.get("/users", response_model=List[dict])
def list_users(db: Session = Depends(get_db), current_user=Depends(admin_required)):
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username, "email": u.email} for u in users]

@router.get("/users/{user_id}", response_model=dict)
def get_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(admin_required)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return {"id": user.id, "username": user.username, "email": user.email}

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(admin_required)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}

# --- GROUPS ---

@router.get("/groups", response_model=List[dict])
def list_groups(db: Session = Depends(get_db), current_user=Depends(admin_required)):
    groups = db.query(Group).all()
    return [{"id": g.id, "name": g.name} for g in groups]

@router.post("/groups")
def create_group(name: str, db: Session = Depends(get_db), current_user=Depends(admin_required)):
    group = Group(name=name)
    db.add(group)
    db.commit()
    db.refresh(group)
    return {"message": "Group created", "id": group.id}

@router.put("/groups/{group_id}")
def update_group(group_id: int, name: str, db: Session = Depends(get_db), current_user=Depends(admin_required)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(404, "Group not found")
    group.name = name
    db.commit()
    return {"message": "Group updated"}

@router.delete("/groups/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db), current_user=Depends(admin_required)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(404, "Group not found")
    db.delete(group)
    db.commit()
    return {"message": "Group deleted"}

# --- PERMISSIONS ---

@router.get("/permissions", response_model=List[dict])
def list_permissions(db: Session = Depends(get_db), current_user=Depends(admin_required)):
    permissions = db.query(Permission).all()
    return [{"id": p.id, "name": p.name, "description": p.description} for p in permissions]

@router.post("/permissions")
def create_permission(name: str, description: str = "", db: Session = Depends(get_db), current_user=Depends(admin_required)):
    permission = Permission(name=name, description=description)
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return {"message": "Permission created", "id": permission.id}

@router.put("/permissions/{permission_id}")
def update_permission(permission_id: int, name: str, description: str = "", db: Session = Depends(get_db), current_user=Depends(admin_required)):
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(404, "Permission not found")
    permission.name = name
    permission.description = description
    db.commit()
    return {"message": "Permission updated"}

@router.delete("/permissions/{permission_id}")
def delete_permission(permission_id: int, db: Session = Depends(get_db), current_user=Depends(admin_required)):
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(404, "Permission not found")
    db.delete(permission)
    db.commit()
    return {"message": "Permission deleted"}

# --- PROXY SERVICES ---

@router.get("/proxys", response_model=List[dict])
def list_proxys(db: Session = Depends(get_db), current_user=Depends(admin_required)):
    proxys = db.query(ProxyService).all()
    return [{"id": p.id, "name": p.name, "base_url": p.base_url, "description": p.description, "enabled": p.enabled} for p in proxys]

@router.post("/proxys")
def create_proxy(name: str, base_url: str, description: str = "", enabled: bool = True, db: Session = Depends(get_db), current_user=Depends(admin_required)):
    proxy = ProxyService(
        name=name,
        base_url=base_url,
        description=description,
        enabled=enabled
    )
    db.add(proxy)
    db.commit()
    db.refresh(proxy)
    return {"message": "Proxy service created", "id": proxy.id}

@router.put("/proxys/{proxy_id}")
def update_proxy(proxy_id: int, name: str = None, base_url: str = None, description: str = None, enabled: bool = None, db: Session = Depends(get_db), current_user=Depends(admin_required)):
    proxy = db.query(ProxyService).filter(ProxyService.id == proxy_id).first()
    if not proxy:
        raise HTTPException(404, "Proxy not found")
    if name is not None:
        proxy.name = name
    if base_url is not None:
        proxy.base_url = base_url
    if description is not None:
        proxy.description = description
    if enabled is not None:
        proxy.enabled = enabled
    db.commit()
    return {"message": "Proxy service updated"}

@router.delete("/proxys/{proxy_id}")
def delete_proxy(proxy_id: int, db: Session = Depends(get_db), current_user=Depends(admin_required)):
    proxy = db.query(ProxyService).filter(ProxyService.id == proxy_id).first()
    if not proxy:
        raise HTTPException(404, "Proxy not found")
    db.delete(proxy)
    db.commit()
    return {"message": "Proxy service deleted"}

# --- SSO PROVIDERS ---

@router.get("/sso_providers", response_model=List[dict])
def list_sso_providers(db: Session = Depends(get_db), current_user=Depends(admin_required)):
    providers = db.query(SSOProvider).all()
    return [{
        "id": p.id,
        "name": p.name,
        "issuer_url": p.issuer_url,
        "client_id": p.client_id,
        "auth_url": p.auth_url,
        "token_url": p.token_url,
        "userinfo_url": p.userinfo_url,
        "scope": p.scope,
        "enabled": p.enabled
    } for p in providers]

@router.post("/sso_providers")
def create_sso_provider(name: str, issuer_url: str, client_id: str = None, client_secret: str = None,
                        auth_url: str = None, token_url: str = None, userinfo_url: str = None, scope: str = 'openid profile email',
                        enabled: bool = True, db: Session = Depends(get_db), current_user=Depends(admin_required)):
    provider = SSOProvider(
        name=name,
        issuer_url=issuer_url,
        client_id=client_id,
        client_secret=client_secret,
        auth_url=auth_url,
        token_url=token_url,
        userinfo_url=userinfo_url,
        scope=scope,
        enabled=enabled
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return {"message": "SSO provider created", "id": provider.id}

@router.put("/sso_providers/{provider_id}")
def update_sso_provider(provider_id: int, name: str = None, issuer_url: str = None, client_id: str = None,
                        client_secret: str = None, auth_url: str = None, token_url: str = None,
                        userinfo_url: str = None, scope: str = None, enabled: bool = None,
                        db: Session = Depends(get_db), current_user=Depends(admin_required)):
    provider = db.query(SSOProvider).filter(SSOProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(404, "SSO provider not found")
    if name is not None:
        provider.name = name
    if issuer_url is not None:
        provider.issuer_url = issuer_url
    if client_id is not None:
        provider.client_id = client_id
    if client_secret is not None:
        provider.client_secret = client_secret
    if auth_url is not None:
        provider.auth_url = auth_url
    if token_url is not None:
        provider.token_url = token_url
    if userinfo_url is not None:
        provider.userinfo_url = userinfo_url
    if scope is not None:
        provider.scope = scope
    if enabled is not None:
        provider.enabled = enabled
    db.commit()
    return {"message": "SSO provider updated"}

@router.delete("/sso_providers/{provider_id}")
def delete_sso_provider(provider_id: int, db: Session = Depends(get_db), current_user=Depends(admin_required)):
    provider = db.query(SSOProvider).filter(SSOProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(404, "SSO provider not found")
    db.delete(provider)
    db.commit()
    return {"message": "SSO provider deleted"}