Для работы модуля требуется легковесная криптографическая библиотека. Добавьте её в ваш requirements.txt: pyotp==2.9.0.

🎛️ Интеграция 2FA-модуля в ваш каркас server.py
Чтобы этот модуль заработал в составе общей SaaS-платформы на Reg.ru [server.py]:
Скопируйте этот код и сохраните его как src/utils/security_2fa.py [Dockerfile]
.Откройте ваш основной файл src/server.py [server.py]
и в самом верху (где идут импорты) подключите созданный роутер:
"""
from src.utils.security_2fa import router as auth_2fa_router

# Вставляем роутер в FastAPI приложение
app.include_router(auth_2fa_router)

"""
# Вставляем роутер в FastAPI приложение
app.include_router(auth_2fa_router)


Используйте код с осторожностью.

После этого в вашем интерактивном Swagger-интерфейсе (http://localhost:8000/docs)
появится новый полноценный раздел «Контур Безопасности ИБ (2FA)», защищающий доступ к платформе
[main.py, server.py].
