import os
import logging
import random
from aiohttp import web
from aiogram import Bot
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

from config import nalogo_config, sub_config
from service.nalog import create_simple_receipt
from handlers.keyboards import day_word
from service.remna_cmds import remna
from database.db import database


logger = logging.getLogger(__name__)

NALOGO_ACTIVE = nalogo_config.active

suffix = {
    "1": "",
    "3": "а",
    "12": "ев"
}


kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text='Инструкция', 
            callback_data='manual', 
            style='success', 
            icon_custom_emoji_id='5258328383183396223'
        )
    ],
    [
        InlineKeyboardButton(
            text='Подписки', 
            callback_data='subs', 
            style='primary', 
            icon_custom_emoji_id="5226513232549664618"
        )
    ],
    [
        InlineKeyboardButton(
            text='В меню', 
            callback_data='menu', 
            icon_custom_emoji_id='5257963315258204021'
        )
    ]
])

ref_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text='Подписки', 
            callback_data='subs', 
            style='success', 
            icon_custom_emoji_id="5226513232549664618"
        )
    ],
    [
        InlineKeyboardButton(
            text='Реферальная система',
            callback_data='ref_system',
            style='primary',
            icon_custom_emoji_id='5258165702707125574'
        )
    ],
    [
        InlineKeyboardButton(
            text='В меню', 
            callback_data='menu', 
            icon_custom_emoji_id='5257963315258204021'
        )
    ]
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

        if event != "payment.succeeded":
            return web.Response(text="ignored")

        if await database.payment.is_processed(payment_id):
            return web.Response(text="ignored")
        
        await database.payment.mark_processed(payment_id)

        metadata = payment.get("metadata", {})

        user_id = int(metadata["user_id"])
        username = metadata["username"]
        month = metadata["month"]
        uuid = metadata.get("uuid","")

        logger.info(f"Успешный платёж {payment_id} от пользователя {username}")

        bonus_days = 0

        user = await database.users.get_user(user_id)
        referral_from = int(user["referral_from"])

        if referral_from and sub_config.ref_bonus_days and not user["has_payed_sub"]:
            bonus_days = sub_config.ref_bonus_days
            subs = await remna.user_name(referral_from)

            for _, ref_uuid in subs.items():
                await remna.update_user(
                    uuid=str(ref_uuid),
                    days=bonus_days
                )

            await database.users.update_ref_count(referral_from)

            text = f'Вы получили {bonus_days} {day_word(bonus_days)} ко всем вашим подпискам за пользователя {username}'

            await bot.send_photo(
                chat_id=referral_from,
                photo=FSInputFile(get_random_photo()),
                caption=f"<b>— — Рефералка — —</b>\n\n\n{text}", 
                reply_markup=ref_kb,
                parse_mode="HTML"
            )

        add_text = f" + {bonus_days} {day_word(bonus_days)}" if bonus_days else ''

        if not uuid:
            sub = await remna.create_user(
                username=username, 
                tg_id=str(user_id), 
                month=int(month),
                days=bonus_days,
                traffic=sub_config.base_traffic, 
                device_limit=sub_config.base_devices
            )
            text = f"Ваша подписка на {month} месяц{suffix[month]}{add_text}:\n\n{sub}"
            logger.info("Подписка удачно создана")

        else:
            sub_name = await remna.update_user(
                uuid=uuid, 
                month=int(month),
                days=bonus_days,
                traffic=sub_config.base_traffic,
                device_limit=sub_config.base_devices
            )
            text = f"Подписка {sub_name} продлена на {month} месяц{suffix[month]}{add_text}!"
            logger.info(text)

        await bot.send_photo(
            chat_id=user_id,
            photo=FSInputFile(get_random_photo()),
            caption=f"<b>— — Оплата прошла успешно! — —</b>\n\n\n{text}", 
            reply_markup=kb,
            parse_mode="HTML"
        )

        await database.users.activate_sub(user_id)

        if NALOGO_ACTIVE:
            await create_simple_receipt(month=month, user=str(user_id))

        return web.Response(text="ok")

    except Exception:
        logger.exception("Ошибка вебхука")
        return web.Response(status=500, text="error")