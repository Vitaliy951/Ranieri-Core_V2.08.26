import os
import httpx
from typing import Optional

KONTUR_API_KEY = os.getenv("KONTUR_API_KEY")
KONTUR_API_URL = os.getenv("KONTUR_API_URL", "https://api.kontur.ru")

class KonturAdapter:
    @staticmethod
    async def get_inn_info(inn: str) -> dict:
        """Получение данных о компании по ИНН (налоговый статус, задолженности)."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{KONTUR_API_URL}/v1/inn",
                headers={"Authorization": f"Bearer {KONTUR_API_KEY}"},
                json={"inn": inn}
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def get_fssp_debts(full_name: str, birth_date: str) -> float:
        """Проверка долгов в ФССП по ФИО и дате рождения."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{KONTUR_API_URL}/v1/fssp",
                headers={"Authorization": f"Bearer {KONTUR_API_KEY}"},
                json={"full_name": full_name, "birth_date": birth_date}
            )
            data = resp.json()
            return float(data.get("total_debt", 0))
