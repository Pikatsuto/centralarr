def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_auth_base_route(client):
    response = client.get("/api/auth/")
    # On peut s'attendre à 405 (Method Not Allowed) si pas de GET mais route existe
    assert response.status_code in (404, 405)

def test_proxy_base_route(client):
    response = client.get("/api/proxy/")
    # Normalement 404 car service_name obligatoire
    assert response.status_code == 404

def test_crud_base_route(client):
    response = client.get("/api/crud/")
    # Sans authentification, peut être 401 ou 403 ou 404
    assert response.status_code in (401, 403, 404)