import asyncio
import logging
import httpx

from lib.nalogo import Client
from lib.nalogo import UnauthorizedException

from config import nalogo_config, payment_config


logger = logging.getLogger(__name__)

inn = nalogo_config.inn
password = nalogo_config.password
proxy = nalogo_config.proxy
ONE_MONTH = payment_config.one_month
THREE_MONTHS = payment_config.three_month
ONE_YEAR = payment_config.one_year


price_list = {"1": ONE_MONTH, "3": THREE_MONTHS, "12": ONE_YEAR}
suffix = {"1": "", "3": "а", "12": "ев"}


async def create_simple_receipt(month: int, user: str):
    """Формирует и отправляет чек в налоговую. Принимает количество месяцев подписки,
    ищет соответствующую цену, а также добавляет в чек TELEGRAM ID клиента"""

    client = Client(
        base_url="https://lknpd.nalog.ru/api",
        storage_path="app/handlers/tokens.json",
        device_id="my-device-123",
        proxy=proxy
    )

    if not await client.get_access_token():
        await client.create_new_access_token(inn, password)

    for att in range(1, 4):
        try:
            result = await client.income().create(
                name=f"Оплата подписки на {month} месяц{suffix[str(month)]}. ID пользователя: {user}",
                amount=price_list[str(month)], # цена
                quantity=1
            )
            logger.info(f"Удачное формирование чека на сумму {price_list[str(month)]}. ID пользователя: {user}")
            return result["approvedReceiptUuid"]

        except UnauthorizedException:
            logger.error("Токен недействителен, получаем новый...")
            await client.create_new_access_token(inn, password)

        except httpx.ProxyError:
            logger.error("Неправильный username или пароль у прокси")
        
        except Exception as e:
            logger.exception(f"Прокси упал, попытка достучаться до прокси {att}/3")
            await asyncio.sleep(2)

    return None