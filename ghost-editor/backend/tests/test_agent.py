import pytest

def test_trigger_agent(client):
    response = client.post("/api/agent/trigger/1")
    assert response.status_code == 200
    assert response.json()["status"] == "triggered"

def test_list_jobs_empty(client):
    response = client.get("/api/agent/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_job_status_not_found(client):
    response = client.get("/api/agent/status/999")
    assert response.status_code == 404
