import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models import ProxyService
from backend.database import Base, engine, SessionLocal
from unittest.mock import patch
from httpx import Response as HTTPXResponse

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

def test_proxy_service_not_found(client):
    resp = client.get("/api/proxy/nonexistentservice/")
    assert resp.status_code == 404
    assert "not found" in resp.text.lower()

@patch('backend.proxy.httpx.AsyncClient.request')
def test_proxy_service_http_success(mock_request, client, db_session):
    # Setup proxy service in DB
    service = ProxyService(name="testservice", base_url="http://example.com", enabled=True)
    db_session.add(service)
    db_session.commit()

    # Mock httpx response
    mock_resp = HTTPXResponse(
        status_code=200,
        content=b"<html><body>Test page</body></html>",
        headers={"Content-Type": "text/html"}
    )
    mock_request.return_value = mock_resp

    resp = client.get("/api/proxy/testservice/")

    assert resp.status_code == 200
    # Check injected JS script is present
    assert b'<script src="/static/telecommande.js"></script>' in resp.content
    # Content length changed due to injection
    assert len(resp.content) > len(mock_resp.content)

@patch('backend.proxy.httpx.AsyncClient.request')
def test_proxy_service_location_header(mock_request, client, db_session):
    service = ProxyService(name="redirservice", base_url="http://example.com", enabled=True)
    db_session.add(service)
    db_session.commit()
    
    headers = {"Location": "/login"}
    mock_resp = HTTPXResponse(
        status_code=302,
        content=b"",
        headers=headers
    )
    mock_request.return_value = mock_resp

    resp = client.get("/api/proxy/redirservice/somepath")

    assert resp.status_code == 302
    # The Location header should be rewritten to include proxy path prefix
    expected_location = "/api/proxy/redirservice/login"
    assert resp.headers.get("location") == expected_location

def test_proxy_websocket_connection(client, db_session):
    service = ProxyService(name="wsservice", base_url="http://example.com", enabled=True)
    db_session.add(service)
    db_session.commit()

    with client.websocket_connect("/api/proxy/wsservice/wsendpoint") as websocket:
        # No real backend WS server, connection may close fast
        # Testing that the websocket connection is at least established and then closed cleanly
        try:
            data = websocket.receive_bytes(timeout=1)
        except:
            # Expected to timeout or error, so test only connection lifecycle
            pass