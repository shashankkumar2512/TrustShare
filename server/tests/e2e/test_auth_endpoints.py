import pytest
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_login_invalid_credentials():
    response = client.post('/api/auth/login', json={'email': 'admin@test.com', 'password': 'admin'})
    assert response.status_code == 401
