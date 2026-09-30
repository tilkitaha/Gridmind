from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_domain_smoke():
    r = client.post("/v1/dispatch", json={"data": {}})
    assert r.status_code == 200
