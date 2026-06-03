import asyncio
import logging
import httpx

from lib.nalogo import Client
from lib.nalogo import UnauthorizedException

from config import config
from handlers.misc import suffix, price_list


logger = logging.getLogger(__name__)


async def create_simple_receipt(month: int, user: str):
    """Формирует и отправляет чек в налоговую. Принимает количество месяцев подписки,
    ищет соответствующую цену, а также добавляет в чек TELEGRAM ID клиента"""

    client = Client(
        base_url="https://lknpd.nalog.ru/api",
        storage_path="app/handlers/tokens.json",
        device_id="my-device-123",
        proxy=config.nalogo.proxy
    )

    if not await client.get_access_token():
        await client.create_new_access_token(config.nalogo.inn, config.nalogo.password)

    for att in range(1, 4):
        try:
            result = await client.income().create(
                name=f"Оплата подписки на {month} месяц{suffix[str(month)]}. ID пользователя: {user}",
                amount=price_list[str(month)],
                quantity=1
            )
            logger.info(f"Удачное формирование чека на сумму {price_list[str(month)]}. ID пользователя: {user}")
            return result["approvedReceiptUuid"]

        except UnauthorizedException:
            logger.error("Токен недействителен, получаем новый...")
            await client.create_new_access_token(config.nalogo.inn, config.nalogo.password)

        except httpx.ProxyError:
            logger.error("Неправильный username или пароль у прокси")

        except httpx.ReadTimeout:
            logger.info(f"Удачное формирование чека на сумму {price_list[str(month)]}. ID пользователя: {user}")
            break
        
        except Exception:
            logger.exception(f"Прокси упал, попытка достучаться до прокси {att}/3")
            await asyncio.sleep(2)

    return None