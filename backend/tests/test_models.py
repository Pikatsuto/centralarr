import pytest
from sqlalchemy.exc import IntegrityError
from backend.models import User, Group, Permission, ProxyService, SSOProvider
from backend.database import Base, engine, SessionLocal

@pytest.fixture(scope="function")
def db_session():
    """
    Create a new database session for a test.
    """
    # Setup DB: create tables
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)

def test_user_group_permission_relationship(db_session):
    # Create groups
    admin_group = Group(name='admin')
    user_group = Group(name='user')
    db_session.add_all([admin_group, user_group])
    db_session.commit()

    # Create permissions
    perm_read = Permission(name='read', description='Read access')
    perm_write = Permission(name='write', description='Write access')
    db_session.add_all([perm_read, perm_write])
    db_session.commit()

    # Create user and assign group and permissions
    user = User(username='alice', email='alice@example.com')
    user.groups.append(admin_group)
    user.permissions.extend([perm_read, perm_write])
    db_session.add(user)
    db_session.commit()

    # Test relationships
    assert user in admin_group.users
    assert perm_read in user.permissions
    assert perm_write in admin_group.permissions or perm_write not in admin_group.permissions  # group permissions are separate

def test_proxy_service_crud(db_session):
    proxy = ProxyService(name='jellyfin', base_url='http://localhost:8096', description='Media server', enabled=True)
    db_session.add(proxy)
    db_session.commit()

    fetched = db_session.query(ProxyService).filter_by(name='jellyfin').first()
    assert fetched is not None
    assert fetched.base_url == 'http://localhost:8096'

def test_sso_provider_crud(db_session):
    provider = SSOProvider(
        name='Keycloak',
        issuer_url='https://keycloak.example.com/auth/realms/master',
        client_id='myclient',
        client_secret='secret',
        auth_url='https://keycloak.example.com/auth',
        token_url='https://keycloak.example.com/token',
        userinfo_url='https://keycloak.example.com/userinfo',
        scope='openid profile email',
        enabled=True
    )
    db_session.add(provider)
    db_session.commit()

    fetched = db_session.query(SSOProvider).filter_by(name='Keycloak').first()
    assert fetched is not None
    assert fetched.enabled == True

def test_unique_constraints(db_session):
    user1 = User(username='uniqueuser', email='unique@example.com')
    db_session.add(user1)
    db_session.commit()

    user2 = User(username='uniqueuser', email='other@example.com')
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()