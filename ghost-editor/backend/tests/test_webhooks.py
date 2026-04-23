import json
import pytest

def test_github_webhook_ping(client):
    headers = {
        "X-GitHub-Event": "ping",
        "Content-Type": "application/json"
    }
    payload = {"zen": "Keep it simple, stupid."}
    
    response = client.post(
        "/api/webhooks/github",
        headers=headers,
        content=json.dumps(payload)
    )
    
    assert response.status_code == 200
    assert response.json() == {"msg": "pong"}

def test_github_webhook_pull_request(client):
    headers = {
        "X-GitHub-Event": "pull_request",
        "Content-Type": "application/json"
    }
    payload = {
        "action": "opened",
        "number": 1,
        "repository": {
            "full_name": "test/repo"
        }
    }
    
    response = client.post(
        "/api/webhooks/github",
        headers=headers,
        content=json.dumps(payload)
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "processing"
    assert response.json()["event"] == "pull_request"

def test_github_webhook_invalid_signature(client):
    # This should fail if GITHUB_WEBHOOK_SECRET is set in environment
    # For now, verification is skipped if secret is missing in routers/webhooks.py
    headers = {
        "X-GitHub-Event": "ping",
        "X-Hub-Signature-256": "sha256=invalid",
        "Content-Type": "application/json"
    }
    payload = {"msg": "test"}
    
    # We expect 200 if secret is not set, or 403 if it is.
    # Let's check config to see if secret is set.
    from config import GITHUB_WEBHOOK_SECRET
    
    response = client.post(
        "/api/webhooks/github",
        headers=headers,
        content=json.dumps(payload)
    )
    
    if GITHUB_WEBHOOK_SECRET:
        assert response.status_code == 403
    else:
        assert response.status_code == 200
