import pytest
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_list_users():
    response = client.get('/api/users/')
    assert response.status_code == 200
