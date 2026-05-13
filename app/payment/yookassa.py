import base64
import logging
import aiohttp
from uuid import uuid4

from database.payments import create_payment_record
from config import payment_config


logger = logging.getLogger(__name__)


SHOP_ID = payment_config.shop_id
SECRET_KEY = payment_config.secret_key

ONE_MONTH = payment_config.one_month
THREE_MONTHS = payment_config.three_month
ONE_YEAR = payment_config.one_year

YOOKASSA_API_URL = "https://api.yookassa.ru/v3/payments"

suffix = {
    "1": "",
    "3": "а",
    "12": "ев"
}

price_list = {
    "1": ONE_MONTH,
    "3": THREE_MONTHS,
    "12": ONE_YEAR
}


async def create_payment(user_id: int, username: str, month: str, return_url: str, uuid: str | None = None) -> str:
    """Создаёт платёж и возвращает ссылку на оплату"""
    logger.info("Начало формирования платежа")
    payload = {
        "amount": {"value": str(price_list[month]), "currency": "RUB"},

        "capture": True,
        "confirmation": {"type": "redirect", "return_url": return_url},
        "description": (f'{"Продление подписки" if uuid else "Подписка"} на {month} мес.'),

        "metadata": {
            "user_id": str(user_id),
            "username": username,
            "month": month,
            "uuid": uuid or ""
        }
    }

    auth = base64.b64encode(f"{SHOP_ID}:{SECRET_KEY}".encode()).decode()

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

    logger.info(f"Создан платёж {response_data['id']} пользователем {username}")
    await create_payment_record(response_data['id'])

    return response_data["confirmation"]["confirmation_url"]