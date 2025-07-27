import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models import User, Group, Permission, ProxyService, SSOProvider
from backend.database import Base, engine, SessionLocal
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@pytest.fixture(scope="module")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture()
def setup_admin_user(db_session):
    admin_group = Group(name="admin")
    admin_user = User(
        username="admin",
        email="admin@example.com",
        password_hash=pwd_context.hash("adminpass")
    )
    admin_user.groups.append(admin_group)
    db_session.add(admin_group)
    db_session.add(admin_user)
    db_session.commit()
    return admin_user

def get_auth_header(client, username, password):
    response = client.post(
        "/api/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --- Group tests ---

def test_create_group(client, db_session, setup_admin_user):
    headers = get_auth_header(client, "admin", "adminpass")

    response = client.post("/api/crud/groups", json={"name": "testgroup"}, headers=headers)
    assert response.status_code in (200, 201)
    assert "id" in response.json()

def test_list_groups(client, headers=None):
    if headers is None:
        headers = {}

    response = client.get("/api/crud/groups", headers=headers)
    assert response.status_code == 200
    groups = response.json()
    assert isinstance(groups, list)

def test_update_group(client, db_session, setup_admin_user):
    headers = get_auth_header(client, "admin", "adminpass")

    # Create group first
    group_resp = client.post("/api/crud/groups", json={"name": "group_to_update"}, headers=headers)
    group_id = group_resp.json()["id"]

    # Update the group
    update_resp = client.put(f"/api/crud/groups/{group_id}", json={"name": "group_updated"}, headers=headers)
    assert update_resp.status_code == 200
    assert "message" in update_resp.json()

def test_delete_group(client, db_session, setup_admin_user):
    headers = get_auth_header(client, "admin", "adminpass")

    # Create group first
    group_resp = client.post("/api/crud/groups", json={"name": "group_to_delete"}, headers=headers)
    group_id = group_resp.json()["id"]

    # Delete the group
    del_resp = client.delete(f"/api/crud/groups/{group_id}", headers=headers)
    assert del_resp.status_code == 200
    assert "message" in del_resp.json()


# --- Similar tests for Permissions ---

def test_create_permission(client, setup_admin_user):
    headers = get_auth_header(client, "admin", "adminpass")

    response = client.post("/api/crud/permissions", json={"name": "testperm", "description": "Description"}, headers=headers)
    assert response.status_code in (200, 201)
    assert "id" in response.json()

def test_list_permissions(client):
    response = client.get("/api/crud/permissions")
    assert response.status_code == 200

def test_update_permission(client, setup_admin_user):
    headers = get_auth_header(client, "admin", "adminpass")
    # Create permission first
    perm_resp = client.post("/api/crud/permissions", json={"name": "perm_to_update"}, headers=headers)
    perm_id = perm_resp.json()["id"]

    # Update permission
    update_resp = client.put(f"/api/crud/permissions/{perm_id}", json={"description": "Updated description"}, headers=headers)
    assert update_resp.status_code == 200

def test_delete_permission(client, setup_admin_user):
    headers = get_auth_header(client, "admin", "adminpass")
    perm_resp = client.post("/api/crud/permissions", json={"name": "perm_to_delete"}, headers=headers)
    perm_id = perm_resp.json()["id"]

    del_resp = client.delete(f"/api/crud/permissions/{perm_id}", headers=headers)
    assert del_resp.status_code == 200


# --- Proxy Service tests ---

def test_create_proxy_service(client, setup_admin_user):
    headers = get_auth_header(client, "admin", "adminpass")

    response = client.post(
        "/api/crud/proxys",
        json={"name": "testproxy", "base_url": "http://localhost:8096", "description": "desc", "enabled": True},
        headers=headers,
    )
    assert response.status_code in (200, 201)
    assert "id" in response.json()

def test_list_proxy_services(client):
    response = client.get("/api/crud/proxys")
    assert response.status_code == 200

def test_update_proxy_service(client, setup_admin_user):
    headers = get_auth_header(client, "admin", "adminpass")

    proxy_resp = client.post(
        "/api/crud/proxys",
        json={"name": "proxy_to_update", "base_url": "http://localhost"},
        headers=headers,
    )
    proxy_id = proxy_resp.json()["id"]

    update_resp = client.put(
        f"/api/crud/proxys/{proxy_id}",
        json={"description": "Updated desc", "enabled": False},
        headers=headers,
    )
    assert update_resp.status_code == 200

def test_delete_proxy_service(client, setup_admin_user):
    headers = get_auth_header(client, "admin", "adminpass")

    proxy_resp = client.post(
        "/api/crud/proxys", json={"name": "proxy_to_delete", "base_url": "http://localhost"}, headers=headers
    )
    proxy_id = proxy_resp.json()["id"]

    del_resp = client.delete(f"/api/crud/proxys/{proxy_id}", headers=headers)
    assert del_resp.status_code == 200


# --- SSO Provider tests ---

def test_create_sso_provider(client, setup_admin_user):
    headers = get_auth_header(client, "admin", "adminpass")

    response = client.post(
        "/api/crud/sso_providers",
        json={
            "name": "test-sso",
            "issuer_url": "https://issuer.example.com",
            "client_id": "id",
            "client_secret": "secret",
            "auth_url": "https://auth.example.com",
            "token_url": "https://token.example.com",
            "userinfo_url": "https://userinfo.example.com",
            "scope": "openid profile email",
            "enabled": True,
        },
        headers=headers,
    )
    assert response.status_code in (200, 201)
    assert "id" in response.json()

def test_list_sso_providers(client):
    response = client.get("/api/crud/sso_providers")
    assert response.status_code == 200

def test_update_sso_provider(client, setup_admin_user):
    headers = get_auth_header(client, "admin", "adminpass")

    provider_resp = client.post(
        "/api/crud/sso_providers", json={"name": "sso_to_update", "issuer_url": "https://issuer"}, headers=headers
    )
    provider_id = provider_resp.json()["id"]

    update_resp = client.put(
        f"/api/crud/sso_providers/{provider_id}",
        json={"client_id": "new_id", "enabled": False},
        headers=headers,
    )
    assert update_resp.status_code == 200

def test_delete_sso_provider(client, setup_admin_user):
    headers = get_auth_header(client, "admin", "adminpass")

    provider_resp = client.post(
        "/api/crud/sso_providers", json={"name": "sso_to_delete", "issuer_url": "https://issuer"}, headers=headers
    )
    provider_id = provider_resp.json()["id"]

    del_resp = client.delete(f"/api/crud/sso_providers/{provider_id}", headers=headers)
    assert del_resp.status_code == 200