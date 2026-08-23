# API Reference – Ranieri Core SaaS Platform

## Базовый URL
`https://api.ranieri-core.ru/api/v1/saas`

## Аутентификация
Во все запросы необходимо включать заголовок:
`X-API-Key: <ваш_ключ>`

## Эндпоинты

### 1. Пополнение баланса
`POST /billing/topup`

**Параметры** (query):
- `amount` – сумма пополнения (float)

**Пример ответа:**
```json
{
  "status": "SUCCESS",
  "company": "Альфа-Банк",
  "new_balance_rub": 150000.0
}
# REST API REFERENCE: SAAS СКОРИНГ «RANIERI CORE»

Базовый URL промышленного контура: `https://cctech.ru`  
Все запросы должны содержать заголовок авторизации: `X-SaaS-API-Key: <ваш_b2b_токен>`

## 1. Пополнение B2B-баланса лицензии
* **Эндпоинт:** `POST /api/v1/saas/billing/topup`
* **Параметры запроса (Query):** `amount=150000.0`
* **Успешный ответ (200 OK):**
```json
{
  "status": "SUCCESS",
  "company": "ПАО Альфа-Банк",
  "new_balance_rub": 300000.0
}
```

## 2. Комплексный ИИ-скоринг и AVM-оценка залога
* **Эндпоинт:** `POST /api/v1/saas/evaluate`
* **Тело запроса (JSON):**
```json
{
  "client_uid": "CLI-889900",
  "snils": "123-456-789 00",
  "inn_fiz": "771234567890",
  "requested_loan_amount": 6500000.0,
  "declared_property_value": 8500000.0,
  "total_area": 54.5,
  "house_type": "MONOLITH",
  "scoring_type": "PREMIUM"
}
```
* **Успешный ответ (200 OK) с логом ИИ-рассуждений (Explainable AI):**
```json
{
  "timestamp": "2026-08-23T11:20:00Z",
  "scoring_uid": "SAAS-20260823112000",
  "charged_rub": 250.0,
  "remaining_balance_rub": 299750.0,
  "verdict": "APPROVE",
  "ai_reasoning_tree": [
    "Кредитный профиль заемщика стабилен.",
    "Данные СМЭВ 3.0 верифицированы.",
    "Индекс стажа СФР: 0.96. Рисков фрода работодателя не обнаружено."
  ],
  "credit_risk_assessment": {
    "score": 745,
    "probability_of_default": 0.0125,
    "smev_payload": {
      "sfr_verified_income": 145000.0,
      "fssp_active_debts": 0.0
    }
  },
  "property_valuation_lstr": {
    "calculated_fair_value_now": 8345000,
    "predicted_stress_value_3y": 7093250,
    "price_deviation_percent": 1.85,
    "predictive_stress_ltv": 0.72
  }
}
```
