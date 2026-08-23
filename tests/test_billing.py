import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_topup():
    response = client.post(
        "/api/v1/saas/billing/topup",
        headers={"X-API-Key": "bank_alpha_token_123"},
        params={"amount": 10000}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["new_balance_rub"] == 160000.0

def test_insufficient_balance():
    # Используем клиента с малым балансом
    response = client.post(
        "/api/v1/saas/evaluate",
        headers={"X-API-Key": "mfo_bystrodengi_token_456"},
        json={
            "client_uid": "TEST",
            "snils": "111-222-333 44",
            "inn_fiz": "123456789012",
            "requested_loan_amount": 5000000,
            "scoring_type": "PREMIUM"
        }
    )
    assert response.status_code == 402
    assert "Недостаточно средств" in response.text
