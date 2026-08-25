import os
import time
import base64
import hashlib
import hmac
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/auth/2fa", tags=["Контур Безопасности ИБ (2FA)"])

# --- ИМИТАЦИЯ ЗАЩИЩЕННОЙ БАЗЫ ДАННЫХ ПОЛЬЗОВАТЕЛЕЙ (IN-MEMORY) ---
# В продакшене эти секретные ключи (secret_2fa) хранятся в PostgreSQL в зашифрованном виде
USER_SECURITY_DB = {
    "chairman_ranieri": {
        "role": "Chairman of the Board of Directors",
        "secret_2fa": "MFRGGZDFMZTWQ2LK", # Базовый 32-значный Base32 секрет
        "is_2fa_enabled": True
    },
    "chief_accountant": {
        "role": "Chief Accountant",
        "secret_2fa": "OVXW443JNZZXQ5LM",
        "is_2fa_enabled": True
    }
}

# --- PYDANTIC СТРУКТУРЫ ДАННЫХ (SCHEMAS) ---
class Setup2FARequest(BaseModel):
    username: str = Field(..., example="chairman_ranieri")

class Verify2FARequest(BaseModel):
    username: str = Field(..., example="chairman_ranieri")
    totp_code: str = Field(..., min_length=6, max_length=6, example="123456")

# --- КРИПТОГРАФИЧЕСКОЕ ЯДРО 2FA (РЕАЛИЗАЦИЯ RFC 6238 / TOTP) ---
class TOTPEngine:
    """
    Математический движок генерации и верификации одноразовых паролей по времени.
    Разработано ООО 'ЦК Технологии' для импортонезависимых финтех-платформ.
    """
    @staticmethod
    def generate_random_secret() -> str:
        """
        Генерация криптографически стойкого случайного Base32-секрета для нового пользователя
        """
        random_bytes = os.urandom(10)
        return base64.b32encode(random_bytes).decode('utf-8')

    @classmethod
    def calculate_totp(cls, secret: str, time_interval: int = 30) -> str:
        """
        Низкоуровневый расчет текущего 6-значного OTP-кода на основе секретного ключа и времени.
        Использует SHA-1 хэширование согласно стандарту ГОСТ/RFC.
        """
        try:
            key = base64.b32decode(secret, casefold=True)
        except Exception:
            raise ValueError("Критическая ошибка ИБ: Неверный формат Base32 секрета")

        # Получаем текущее количество 30-секундных интервалов, прошедших с 1 января 1970 года
        time_counter = int(time.time() // time_interval)
        bytes_counter = time_counter.to_bytes(8, byteorder='big')

        # Вычисляем HMAC-SHA1 хэш
        hmac_hash = hmac.new(key, bytes_counter, hashlib.sha1).digest()

        # Динамическое смещение (Dynamic Truncation) для извлечения 4-х байт из хэша
        offset = hmac_hash[-1] & 0x0f
        binary_code = ((hmac_hash[offset] & 0x7f) << 24 |
                       (hmac_hash[offset+1] & 0xff) << 16 |
                       (hmac_hash[offset+2] & 0xff) << 8 |
                       (hmac_hash[offset+3] & 0xff))

        # Выделяем последние 6 цифр
        otp = binary_code % 1_000_000
        return str(otp).zfill(6)

    @classmethod
    def verify_code(cls, secret: str, code_to_verify: str, window: int = 1) -> bool:
        """
        Верификация одноразового кода с учетом временного окна (защита от сетевых задержек).
        window = 1 позволяет проверить код из текущего, прошлого и следующего 30-сек интервала.
        """
        current_time = int(time.time())
        time_interval = 30

        for i in range(-window, window + 1):
            check_time = current_time + (i * time_interval)
            # Переопределяем счетчик времени для проверки соседних интервалов
            time_counter = int(check_time // time_interval)
            key = base64.b32decode(secret, casefold=True)
            bytes_counter = time_counter.to_bytes(8, byteorder='big')
            
            hmac_hash = hmac.new(key, bytes_counter, hashlib.sha1).digest()
            offset = hmac_hash[-1] & 0x0f
            binary_code = ((hmac_hash[offset] & 0x7f) << 24 |
                           (hmac_hash[offset+1] & 0xff) << 16 |
                           (hmac_hash[offset+2] & 0xff) << 8 |
                           (hmac_hash[offset+3] & 0xff))
            
            if str(binary_code % 1_000_000).zfill(6) == code_to_verify:
                return True
        return False

# --- API ЭНДПОИНТЫ 2FA КОНТУРА ---

@router.post("/setup", status_code=status.HTTP_201_CREATED)
async def setup_two_factor_auth(payload: Setup2FARequest):
    """
    Шаг 1: Первичная генерация секретного ключа 2FA и URI для генерации QR-кода.
    Вызывается при первом входе топ-менеджера в ЛК.
    """
    username = payload.username
    if username in USER_SECURITY_DB:
        secret = USER_SECURITY_DB[username]["secret_2fa"]
    else:
        # Для нового пользователя генерируем новый секрет
        secret = TOTPEngine.generate_random_secret()
        USER_SECURITY_DB[username] = {"role": "B2B_Partner", "secret_2fa": secret, "is_2fa_enabled": False}

    # Стандартизированная строка URI для распознавания приложениями Google Authenticator / Яндекс Ключ
    otp_auth_uri = f"otpauth://totp/RanieriCore:{username}?secret={secret}&issuer=RanieriCoreHolding"
    
    return {
        "status": "INITIATED",
        "username": username,
        "secret_base32": secret,
        "otpauth_uri": otp_auth_uri,
        "instruction": "Закодируйте 'otpauth_uri' в QR-код и отсканируйте его в приложении Google Authenticator."
    }

@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_two_factor_token(payload: Verify2FARequest):
    """
    Шаг 2: Криптографическая валидация 6-значного токена, введенного пользователем.
    При успехе открывает доступ к ЛК и кнопке ВЕТО.
    """
    username = payload.username
    if username not in USER_SECURITY_DB:
        raise HTTPException(status_code=404, detail="Пользователь не найден в системе безопасности")

    user_data = USER_SECURITY_DB[username]
    is_valid = TOTPEngine.verify_code(user_data["secret_2fa"], payload.totp_code)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Критическая ошибка ИБ: Неверный или просроченный код двухфакторной аутентификации."
        )

    # Меняем внутренний флаг безопасности
    user_data["is_2fa_enabled"] = True

    return {
        "status": "AUTHENTICATED",
        "username": username,
        "role": user_data["role"],
        "token_verdict": "ACCESS_GRANTED_GOST_R_57580"
    }
