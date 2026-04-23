import pytest

def test_create_repo(client):
    payload = {
        "name": "test-repo",
        "url": "https://github.com/test/repo",
        "is_active": True
    }
    response = client.post("/api/repos/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test-repo"
    assert "id" in data

def test_list_repos(client):
    # Create one first
    client.post("/api/repos/", json={"name": "repo1", "url": "url1"})
    
    response = client.get("/api/repos/")
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_get_repo_not_found(client):
    response = client.get("/api/repos/999")
    assert response.status_code == 404
