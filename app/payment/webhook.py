import os
import logging
import random
from aiohttp import web
from aiogram import Bot
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

from config import nalogo_config
from service.nalog import create_simple_receipt
from service.remna_cmds import remna_create_user, update_user
from database.payments import is_payment_processed, update_payment_status, mark_payment_processed


logger = logging.getLogger(__name__)

NALOGO_ACTIVE = nalogo_config.active

suffix = {
    "1": "",
    "3": "а",
    "12": "ев"
}

kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Инструкция', callback_data='manual', style='primary', icon_custom_emoji_id='5258328383183396223')],
    [InlineKeyboardButton(text='В меню', callback_data='menu', icon_custom_emoji_id='5257963315258204021')]
])


def get_random_photo() -> str:
    """Возвращает путь случайного файла из папки photos"""
    files = [photo for photo in os.listdir("app/menu_photos")]

    file = random.choice(files)
    return os.path.join("app/menu_photos", file)


async def yookassa_webhook(request: web.Request):
    bot: Bot = request.app["bot"]
    try:
        data = await request.json()
        logger.info(f"Получен вебхук: {data}")
        event = data.get("event")

        payment = data.get("object", {})
        payment_id = payment.get("id")
        status = payment.get("status")

        await update_payment_status(payment_id, status)

        if event != "payment.succeeded":
            return web.Response(text="ignored")

        if await is_payment_processed(payment_id):
            return web.Response(text="ignored")

        metadata = payment.get("metadata", {})

        user_id = int(metadata["user_id"])
        username = metadata["username"]
        month = metadata["month"]
        uuid = metadata.get("uuid","")

        logger.info(f"Успешный платёж {payment_id} от пользователя {username}")

        if not uuid:
            sub = await remna_create_user(username, str(user_id), int(month))
            text = (f"Ваша подписка на {month} месяц{suffix[month]}:\n\n{sub}")
            logger.info("Подписка удачно создана")

        else:
            sub_name = await update_user(uuid, int(month))
            text = (f"Подписка {sub_name} продлена на {month} месяц{suffix[month]}!")
            logger.info(text)

        await bot.send_photo(chat_id=user_id,
                             photo=FSInputFile(get_random_photo()),
                             caption=f"<b>— — Оплата прошла успешно! — —</b>\n\n\n{text}", 
                             reply_markup=kb,
                             parse_mode="HTML")

        await mark_payment_processed(payment_id)

        if NALOGO_ACTIVE:
            await create_simple_receipt(month=month, user=str(user_id))

        return web.Response(text="ok")

    except Exception:
        logger.exception("Ошибка вебхука")
        return web.Response(status=500, text="error")