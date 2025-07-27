import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models import User, Group, SSOProvider
from backend.database import Base, engine, SessionLocal
from passlib.context import CryptContext
import respx
from httpx import Response
import secrets

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

def test_register_requires_admin(client):
    # Without token, registration forbidden
    response = client.post("/api/auth/register", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "pass1"
    })
    assert response.status_code == 403  # forbidden without token

def test_login_and_me(client, db_session):
    # Add user
    user = User(username="testuser", email="testuser@example.com", password_hash=pwd_context.hash("testpass"))
    db_session.add(user)
    db_session.commit()

    # Login to get token
    headers = get_auth_header(client, "testuser", "testpass")

    # Access protected endpoint /me
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_register_allowed_for_admin(client, db_session, setup_admin_user):
    headers = get_auth_header(client, "admin", "adminpass")

    # Register new user
    response = client.post("/api/auth/register", json={
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "UserPass123"
    }, headers=headers)
    assert response.status_code == 201
    assert "User created" in response.json().get("message", "")

@respx.mock
def test_sso_login_flow(client, db_session, setup_admin_user):
    # Setup fake SSO provider
    sso_provider = SSOProvider(
        name='fakeprovider',
        issuer_url='https://fakeidp.example.com',
        client_id='fake-client-id',
        client_secret='fake-secret',
        auth_url='https://fakeidp.example.com/auth',
        token_url='https://fakeidp.example.com/token',
        userinfo_url='https://fakeidp.example.com/userinfo',
        scope='openid profile email',
        enabled=True
    )
    db_session.add(sso_provider)
    db_session.commit()

    # Simulate state storage by client (normally stored in session)
    fake_state = secrets.token_urlsafe(16)

    # Mock token endpoint
    token_route = respx.post("https://fakeidp.example.com/token").mock(
        return_value=Response(200, json={"access_token": "fake-access-token"})
    )
    # Mock userinfo endpoint
    userinfo_route = respx.get("https://fakeidp.example.com/userinfo").mock(
        return_value=Response(200, json={"email": "sso_user@example.com", "preferred_username": "sso-user"})
    )

    # Simulate SSO callback with code and state
    response = client.get(f"/api/auth/sso/callback/fakeprovider?code=fakecode&state={fake_state}")

    assert response.status_code in (200, 302, 307)
    # Verify user creation
    user = db_session.query(User).filter_by(email="sso_user@example.com").first()
    assert user is not None
    assert user.username == "sso-user"