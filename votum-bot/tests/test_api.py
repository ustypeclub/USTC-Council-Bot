from fastapi.testclient import TestClient
import pytest

from dashboard.app import app


def test_api_requires_auth():
    client = TestClient(app)
    response = client.get("/api/councils/")
    # unauthenticated requests should return 401
    assert response.status_code == 401