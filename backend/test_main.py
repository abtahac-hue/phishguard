from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_combined_warning_signs():
    response = client.post("/analyze", json={
        "text": (
            "Urgent! Your account will be suspended. "
            "Verify your password immediately."
        )
    })

    assert response.status_code == 200
    result = response.json()
    assert result["score"] == 65
    assert result["risk_level"] == "High"
    assert {finding["id"] for finding in result["findings"]} == {
        "urgency", "account_threat", "credential_request"
    }


def test_repeated_urgency_counts_once():
    response = client.post("/analyze", json={
        "text": "Urgent! Act now! Immediately!"
    })

    assert response.json()["score"] == 15
    assert len(response.json()["findings"]) == 1


def test_ordinary_message_has_no_findings():
    response = client.post("/analyze", json={
        "text": "Our study group meets at the library on Friday."
    })

    assert response.json()["score"] == 0
    assert response.json()["findings"] == []


def test_blank_message_is_rejected():
    response = client.post("/analyze", json={"text": "   "})

    assert response.status_code == 422


def test_oversized_message_is_rejected():
    response = client.post("/analyze", json={"text": "a" * 10001})

    assert response.status_code == 422
    