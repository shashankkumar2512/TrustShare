import pytest
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_list_todos():
    response = client.get('/api/todos/')
    assert response.status_code == 200
    assert isinstance(response.json(), list)
