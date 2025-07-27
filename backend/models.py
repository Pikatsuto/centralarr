from sqlalchemy import Table, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# Association tables for many-to-many relationships
user_groups = Table(
    'user_groups',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True)
)

user_permissions = Table(
    'user_permissions',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

group_permissions = Table(
    'group_permissions',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=True)

    groups = relationship('Group', secondary=user_groups, back_populates='users')
    permissions = relationship('Permission', secondary=user_permissions, back_populates='users')

    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"

class Group(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)

    users = relationship('User', secondary=user_groups, back_populates='groups')
    permissions = relationship('Permission', secondary=group_permissions, back_populates='groups')

    def __repr__(self):
        return f"<Group(name={self.name})>"

class Permission(Base):
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)
    description = Column(String(200), nullable=True)

    users = relationship('User', secondary=user_permissions, back_populates='permissions')
    groups = relationship('Group', secondary=group_permissions, back_populates='permissions')

    def __repr__(self):
        return f"<Permission(name={self.name})>"

class ProxyService(Base):
    __tablename__ = 'proxy_services'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    base_url = Column(String(200), nullable=False)
    description = Column(String(200), nullable=True)
    enabled = Column(Boolean, default=True)

    def __repr__(self):
        return f"<ProxyService(name={self.name}, enabled={self.enabled})>"

class SSOProvider(Base):
    __tablename__ = 'sso_providers'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)
    issuer_url = Column(String(200), nullable=False)
    client_id = Column(String(200), nullable=True)
    client_secret = Column(String(200), nullable=True)
    auth_url = Column(String(200), nullable=True)
    token_url = Column(String(200), nullable=True)
    userinfo_url = Column(String(200), nullable=True)
    scope = Column(String(200), default='openid profile email')
    enabled = Column(Boolean, default=True)

    def __repr__(self):
        return f"<SSOProvider(name={self.name}, enabled={self.enabled})>"