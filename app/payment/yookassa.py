import base64
import logging
import aiohttp
from uuid import uuid4

from database.db import database
from config import config

from handlers.misc import suffix, price_list


logger = logging.getLogger(__name__)
YOOKASSA_API_URL = "https://api.yookassa.ru/v3/payments"


async def create_payment(user_id: int, username: str, month: str, return_url: str, uuid: str | None = None) -> str:
    """Создаёт платёж и возвращает ссылку на оплату"""
    logger.info("Начало формирования платежа")

    sub_count = 1
    if uuid and uuid.isdigit():
        sub_count = int(uuid)

    payload = {
        "amount": {"value": str(int(price_list[month]) * sub_count), "currency": "RUB"},

        "capture": True,
        "confirmation": {"type": "redirect", "return_url": return_url},
        "description": (f'{"Продление подписки" if uuid else "Подписка"} на {month} месяц{suffix[month]}'),

        "metadata": {
            "user_id": str(user_id),
            "username": username,
            "month": month,
            "uuid": uuid or ""
        }
    }

    auth = base64.b64encode(f"{config.yookassa.shop_id}:{config.yookassa.secret_key}".encode()).decode()

    headers = {
        "Authorization": f"Basic {auth}",
        "Idempotence-Key": str(uuid4()),
        "Content-Type": "application/json"
    }

    timeout = aiohttp.ClientTimeout(total=1)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for i in range(10):
            try:
                async with session.post(
                    YOOKASSA_API_URL,
                    json=payload,
                    headers=headers
                ) as response:
                    response_data = await response.json()

                    if response.status not in (200, 201):
                        logger.error(
                            f"Ошибка YooKassa: {response.status} | {response_data}")

                        raise Exception(f"Ошибка юкассы: {response_data}")
            except TimeoutError:
                if i < 9:
                    logger.info(f"Таймаут, попытка {i}, пробуем снова")
                else:
                    raise TimeoutError("Таймаут. Скорее всего, проблема в вашем сервере💀")

    logger.info(f"Сформирован платёж {response_data['id']} пользователем {username}")
    await database.payment.record_create(response_data['id'])

    return response_data["confirmation"]["confirmation_url"]