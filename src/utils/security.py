import os
import hashlib
import hmac
from functools import wraps
from fastapi import HTTPException, Header

SECRET_KEY = os.getenv("SECRET_KEY", "change_this_in_production")

def verify_signature(payload: dict, signature: str) -> bool:
    """Проверка подписи запроса (для защиты от подделки)."""
    computed = hmac.new(
        SECRET_KEY.encode(),
        msg=str(sorted(payload.items())).encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed, signature)

def require_api_key(api_key: str = Header(...)):
    """Декоратор для проверки API-ключа (используется в server.py)."""
    # В реальности проверка по БД или кешу
    if api_key not in ["bank_alpha_token_123", "mfo_bystrodengi_token_456"]:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key
