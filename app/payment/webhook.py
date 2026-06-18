import logging
from aiohttp import web
from aiogram import Bot
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

from config import config
from service.nalog import create_simple_receipt
from handlers.misc import day_word, suffix, get_random_photo
from service.remna import remna
from database.db import database


logger = logging.getLogger(__name__)


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
        amount = payment["amount"]["value"]
        income_amount = payment["income_amount"]["value"]

        logger.info(f"Успешный платёж {payment_id} от пользователя {username}")

        bonus_days = 0
        sub_count = 1

        user = await database.users.get_user(user_id)
        referral_from = int(user["referral_from"]) if user["referral_from"] else None

        if referral_from and config.subscription.ref_bonus_days and not user["has_payed_sub"]:
            bonus_days = config.subscription.ref_bonus_days
            subs = await remna.user_name(referral_from)
            ref_sub = ''

            for _, ref_uuid in subs.items():
                ref_sub = ref_sub if ref_sub else _
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

        log_add_text = f" + {bonus_days} {day_word(bonus_days)} за пользователя {ref_sub}" if bonus_days else ''

        add_text = f" + {bonus_days} {day_word(bonus_days)} за пользователя <a href='tg://user?id={referral_from}'>{ref_sub}</a>" if bonus_days else ''

        if not uuid:
            sub = await remna.create_user(
                username=username, 
                tg_id=str(user_id),
                month=int(month),
                days=bonus_days,
                traffic=config.subscription.base_traffic, 
                device_limit=config.subscription.base_devices
            )
            text = f"Ваша подписка на {month} месяц{suffix[month]}{log_add_text}:\n\n{sub}"
            emoji = '<tg-emoji emoji-id="5258165702707125574">⭐️</tg-emoji>'
            logger.info(f"Подписка {username} на {month} месяц{suffix[month]} удачно создана")
            for_log_text = 'подписку'

        else:
            uuids = []
            one = True
            emoji = '<tg-emoji emoji-id="5258185631355378853">⭐️</tg-emoji>'

            if uuid.isdigit():
                one = False
                sub_count = int(uuid)
                lst = await remna.user_name(tg_id=user_id)
                for _, uuid in lst.items():
                    uuids.append(str(uuid))
            else:
                uuids.append(uuid)

            for uuid in uuids:
                sub_name = await remna.update_user(
                    uuid=uuid,
                    month=int(month),
                    days=bonus_days,
                    traffic=config.subscription.base_traffic,
                    device_limit=config.subscription.base_devices
                )
                text = f"Подписка {sub_name} продлена на {month} месяц{suffix[month]}!"
                logger.info(text)
            
            for_log_text = f'продление подписки {sub_name}'

            if not one:
                text = f"Ваши подписки продлены на {month} месяц{suffix[month]}!"
                emoji = '<tg-emoji emoji-id="5359719332542718652">💎</tg-emoji>'
                for_log_text = f'продление {sub_count} подписок'

        await bot.send_photo(
            chat_id=user_id,
            photo=FSInputFile(get_random_photo()),
            caption=f"<b>— — Оплата прошла успешно! — —</b>\n\n\n{text}", 
            reply_markup=kb,
            parse_mode="HTML"
        )
        
        await database.users.activate_sub(user_id)

        a_link = f'<a href="tg://user?id={user_id}">' if username.isdigit() else f'<a href="tg://resolve?domain={username}">'

        log_text = '<b>— — Новая покупка — —</b>\n\n'\
        f'{emoji} Пользователь {a_link}<b>{username}</b></a> оплатил {for_log_text} на {month} месяц{suffix[month]}{add_text}!\n\n'\
        f'<tg-emoji emoji-id="5258336354642697821">⚡️</tg-emoji> Сумма оплаты: {amount} руб.\n'\
        f'<tg-emoji emoji-id="5357069174512303778">✅</tg-emoji> Сумма с учётом комиссии: {income_amount} руб.'

        if config.telegram.log_chat_id:
            await bot.send_message(
                chat_id=config.telegram.log_chat_id,
                message_thread_id=config.telegram.log_payment_topic_id,
                text=log_text,
                parse_mode='HTML'
            )

        logger.info(f'Пользователь {username} оплатил {for_log_text} на {month} месяц{suffix[month]}{log_add_text}!')

        if config.nalogo.active:
            await create_simple_receipt(month=month, user_id=str(user_id), sub_count=sub_count)

        return web.Response(text="ok")

    except Exception:
        logger.exception("Ошибка вебхука")
        return web.Response(status=500, text="error")