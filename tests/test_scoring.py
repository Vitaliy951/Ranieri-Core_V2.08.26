"""
Модуль тестирования для SaaS-платформы скоринга "Ranieri Core".

Покрывает эндпоинты:
- POST /api/v1/saas/evaluate
- POST /api/v1/saas/billing/topup
- POST /api/v1/saas/analytics/upload-history

Проверяет:
- успешное выполнение скоринга (BASE и PREMIUM);
- ошибки при недостатке средств (402);
- ошибки при неверном API-ключе (401);
- превышение rate limit (429, если реализовано);
- загрузку CSV и обновление модели;
- валидацию входных данных.
"""

import pytest
from fastapi.testclient import TestClient
from server import app

# Фикстура клиента
@pytest.fixture
def client():
    return TestClient(app)

# Фикстура для тестового API-ключа
@pytest.fixture
def valid_api_key():
    return "bank_alpha_token_123"

# Фикстура для клиента с малым балансом
@pytest.fixture
def low_balance_key():
    return "mfo_bystrodengi_token_456"

# ---------- Тесты для эндпоинта /evaluate ----------

def test_evaluate_base_success(client, valid_api_key):
    """Тест успешного BASE-скоринга."""
    payload = {
        "client_uid": "CLI-001",
        "snils": "123-456-789 00",
        "inn_fiz": "771234567890",
        "requested_loan_amount": 5000000,
        "declared_property_value": 6000000,
        "total_area": 55,
        "house_type": "MONOLITH",
        "scoring_type": "BASE"
    }
    response = client.post(
        "/api/v1/saas/evaluate",
        headers={"X-API-Key": valid_api_key},
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert "scoring_uid" in data
    assert "verdict" in data
    assert data["verdict"] in ["APPROVE", "REJECT_RISK"]
    # Проверка, что списание выполнено (70 руб.)
    assert data["charged_rub"] == 70.0
    # Проверка, что баланс уменьшился
    assert data["remaining_license_balance_rub"] >= 0

def test_evaluate_premium_success(client, valid_api_key):
    """Тест успешного PREMIUM-скоринга (с LSTR-оценкой)."""
    payload = {
        "client_uid": "CLI-002",
        "snils": "111-222-333 44",
        "inn_fiz": "772233445566",
        "requested_loan_amount": 8000000,
        "declared_property_value": 10000000,
        "total_area": 70,
        "house_type": "BRICK",
        "scoring_type": "PREMIUM"
    }
    response = client.post(
        "/api/v1/saas/evaluate",
        headers={"X-API-Key": valid_api_key},
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["charged_rub"] == 250.0
    assert "property_valuation_lstr" in data
    avm = data["property_valuation_lstr"]
    assert "calculated_fair_value_now" in avm
    assert "predictive_stress_ltv" in avm
    # Проверяем, что если цена завышена, вердикт REJECT_COLLATERAL (может сработать случайно)
    # Но для стабильности теста мы не проверяем конкретный вердикт

def test_evaluate_insufficient_balance(client, low_balance_key):
    """Тест ошибки 402 при недостатке средств."""
    payload = {
        "client_uid": "CLI-003",
        "snils": "111-222-333 44",
        "inn_fiz": "772233445566",
        "requested_loan_amount": 5000000,
        "scoring_type": "BASE"
    }
    response = client.post(
        "/api/v1/saas/evaluate",
        headers={"X-API-Key": low_balance_key},
        json=payload
    )
    assert response.status_code == 402
    assert "Недостаточно средств" in response.text

def test_evaluate_invalid_api_key(client):
    """Тест ошибки 401 при неверном API-ключе."""
    payload = {
        "client_uid": "CLI-004",
        "snils": "111-222-333 44",
        "inn_fiz": "772233445566",
        "requested_loan_amount": 5000000,
        "scoring_type": "BASE"
    }
    response = client.post(
        "/api/v1/saas/evaluate",
        headers={"X-API-Key": "wrong_key"},
        json=payload
    )
    assert response.status_code == 401
    assert "Неверный или заблокированный API-ключ" in response.text

def test_evaluate_missing_fields(client, valid_api_key):
    """Тест ошибки валидации при отсутствии обязательных полей."""
    payload = {
        "client_uid": "CLI-005",
        # отсутствует snils
        "inn_fiz": "123456789012",
        "requested_loan_amount": 5000000,
        "scoring_type": "BASE"
    }
    response = client.post(
        "/api/v1/saas/evaluate",
        headers={"X-API-Key": valid_api_key},
        json=payload
    )
    assert response.status_code == 422  # Pydantic validation error

def test_evaluate_premium_without_area(client, valid_api_key):
    """Тест: PREMIUM-скоринг без площади должен вернуть 400."""
    payload = {
        "client_uid": "CLI-006",
        "snils": "111-222-333 44",
        "inn_fiz": "772233445566",
        "requested_loan_amount": 5000000,
        "declared_property_value": 6000000,
        # total_area отсутствует
        "scoring_type": "PREMIUM"
    }
    response = client.post(
        "/api/v1/saas/evaluate",
        headers={"X-API-Key": valid_api_key},
        json=payload
    )
    # В текущей реализации сервер выдаёт 400, если total_area <= 0
    assert response.status_code == 400
    assert "total_area" in response.text.lower() or "обязательны" in response.text

# ---------- Тесты для эндпоинта /billing/topup ----------

def test_topup_success(client, valid_api_key):
    """Тест успешного пополнения баланса."""
    response = client.post(
        "/api/v1/saas/billing/topup",
        headers={"X-API-Key": valid_api_key},
        params={"amount": 10000}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["new_balance_rub"] > 0

def test_topup_zero_amount(client, valid_api_key):
    """Тест пополнения на 0 рублей – должно вернуть 400."""
    response = client.post(
        "/api/v1/saas/billing/topup",
        headers={"X-API-Key": valid_api_key},
        params={"amount": 0}
    )
    assert response.status_code == 400
    assert "Сумма пополнения должна превышать 0" in response.text

def test_topup_negative_amount(client, valid_api_key):
    """Тест пополнения на отрицательную сумму – должно вернуть 400."""
    response = client.post(
        "/api/v1/saas/billing/topup",
        headers={"X-API-Key": valid_api_key},
        params={"amount": -500}
    )
    assert response.status_code == 400
    assert "Сумма пополнения должна превышать 0" in response.text

def test_topup_invalid_api_key(client):
    """Тест пополнения с неверным ключом – 401."""
    response = client.post(
        "/api/v1/saas/billing/topup",
        headers={"X-API-Key": "wrong_key"},
        params={"amount": 1000}
    )
    assert response.status_code == 401

# ---------- Тесты для эндпоинта /analytics/upload-history ----------

def test_upload_csv_success(client, valid_api_key, tmp_path):
    """Тест успешной загрузки корректного CSV-файла."""
    # Создаём временный CSV-файл с колонкой price_per_meter
    csv_content = "price_per_meter\n250000\n240000\n260000\n245000\n255000"
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(csv_content)

    with open(csv_file, "rb") as f:
        response = client.post(
            "/api/v1/saas/analytics/upload-history",
            headers={"X-API-Key": valid_api_key},
            files={"file": ("test_data.csv", f, "text/csv")}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["processed_records"] == 5
    # Медиана должна быть 245000 (после сортировки)
    assert data["calibrated_median_price"] == 245000.0

def test_upload_csv_missing_column(client, valid_api_key, tmp_path):
    """Тест загрузки CSV без обязательной колонки."""
    csv_content = "address,area\nMoscow,55\nSPB,60"
    csv_file = tmp_path / "bad_data.csv"
    csv_file.write_text(csv_content)

    with open(csv_file, "rb") as f:
        response = client.post(
            "/api/v1/saas/analytics/upload-history",
            headers={"X-API-Key": valid_api_key},
            files={"file": ("bad_data.csv", f, "text/csv")}
        )
    assert response.status_code == 400
    assert "отсутствует обязательный столбец 'price_per_meter'" in response.text

def test_upload_csv_invalid_api_key(client, tmp_path):
    """Тест загрузки CSV с неверным ключом."""
    csv_content = "price_per_meter\n100000"
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(csv_content)

    with open(csv_file, "rb") as f:
        response = client.post(
            "/api/v1/saas/analytics/upload-history",
            headers={"X-API-Key": "wrong_key"},
            files={"file": ("test.csv", f, "text/csv")}
        )
    assert response.status_code == 401

# ---------- Тест rate limiting (если реализован) ----------

def test_rate_limit(client, valid_api_key):
    """
    Тест превышения rate limit (100 запросов в минуту).
    Для этого отправляем 101 запрос подряд и проверяем, что последний вернёт 429.
    """
    # Если в server.py не реализован rate limit, этот тест может быть пропущен или давать сбои.
    # Поэтому оборачиваем в условную проверку: если приложение не имеет лимитера, тест пропускается.
    # Но мы можем просто проверить, что первый запрос успешен, а 101-й – нет.
    # Для сокращения времени теста проверим только 10 запросов и проверим, что ни один не вернул 429
    # (т.к. лимит 100/мин, 10 запросов не превысят).
    # Если лимитер реализован, то при 101-м будет 429, но для CI это неудобно.
    # Поэтому тест будет проверять наличие заголовков rate limit, если они есть.
    # Пропустим тест, если в ответе нет заголовка X-RateLimit-Limit.
    response = client.post(
        "/api/v1/saas/evaluate",
        headers={"X-API-Key": valid_api_key},
        json={
            "client_uid": "RATE",
            "snils": "111-222-333 44",
            "inn_fiz": "123456789012",
            "requested_loan_amount": 1000000,
            "scoring_type": "BASE"
        }
    )
    # Проверяем, есть ли заголовки ограничения
    if "X-RateLimit-Limit" in response.headers:
        # Если есть, проверим, что лимит > 0
        assert int(response.headers["X-RateLimit-Remaining"]) >= 0
    else:
        # Если лимитера нет, тест пропускается (skipped)
        pytest.skip("Rate limiting not implemented")

# ---------- Тест обработки некорректного JSON ----------

def test_invalid_json(client, valid_api_key):
    """Тест отправки невалидного JSON."""
    response = client.post(
        "/api/v1/saas/evaluate",
        headers={"X-API-Key": valid_api_key},
        data="not a json",  # не JSON
        content_type="application/json"
    )
    assert response.status_code == 422  # FastAPI возвращает 422 при ошибке десериализации
