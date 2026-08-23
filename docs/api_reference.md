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
