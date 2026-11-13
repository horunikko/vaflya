import logging
from aiohttp import web
from aiogram import Bot

from config import config
from service.nalog import create_simple_receipt
from handlers.misc import day_word, suffix, get_random_photo, send_to_user
from service.remna import remna
from database.db import database

from .payment_misc import kb, ref_kb, WebhookData

logger = logging.getLogger(__name__)


async def yookassa_webhook(request: web.Request):
    bot: Bot = request.app["bot"]
    try:
        data = WebhookData(**(await request.json()))
        logger.info(f"Получен вебхук: {data}")

        payment = data.object

        if data.event != "payment.succeeded":
            return web.Response(text="ignored")

        if await database.payment.is_processed(payment.id):
            return web.Response(text="ignored")
        
        await database.payment.mark_processed(payment.id)

        user_id = data.object.metadata.user_id
        username = data.object.metadata.username
        month = data.object.metadata.month
        remna_username = data.object.metadata.remna_username
        amount = data.object.amount.value
        income_amount = data.object.income_amount.value

        logger.info(f"Успешный платёж {payment.id} от пользователя {username}")

        bonus_days = 0
        sub_count = 1

        user = await database.users.get_user(user_id)

        emoji = '<tg-emoji emoji-id="5258165702707125574">⭐️</tg-emoji>'

        if user.referral_from and config.subscription.ref_bonus_days and not user.has_payed_sub:
            bonus_days = config.subscription.ref_bonus_days
            subs = await remna.user_name(user.referral_from)

            for ref_username in subs:
                await remna.update_user(
                    username=ref_username,
                    days=bonus_days
                )

            await database.users.update_ref_count(user.referral_from)

            text = f'Вы получили {bonus_days} {day_word(bonus_days)} ко всем вашим подпискам за пользователя {username}'

            await send_to_user(
                bot=bot,
                user=user.referral_from,
                text=text, 
                kb=ref_kb
            )

        log_add_text = f" + {bonus_days} {day_word(bonus_days)} за пользователя {subs[0]}" if bonus_days else ''

        add_text = f" + {bonus_days} {day_word(bonus_days)} за пользователя <a href='tg://user?id={user.referral_from}'>{subs[0]}</a>" if bonus_days else ''

        if not remna_username:
            sub = await remna.create_user(
                username=username, 
                tg_id=str(user_id),
                month=int(month),
                days=bonus_days,
                traffic=config.subscription.base_traffic, 
                device_limit=config.subscription.base_devices
            )
            text = f"Ваша подписка на {month} месяц{suffix[month]}{log_add_text}:\n\n{sub}"
            logger.info(f"Подписка {username} на {month} месяц{suffix[month]} удачно создана")
            for_log_text = 'подписку'

        else:
            usernames = []
            one = True

            if user.has_payed_sub:
                emoji = '<tg-emoji emoji-id="5258185631355378853">⭐️</tg-emoji>'

            if remna_username.startswith("$"):
                one = False
                sub_count = int(remna_username.removeprefix("$"))
                for us_name in await remna.user_name(tg_id=user_id):
                    usernames.append(us_name)
            else:
                usernames.append(remna_username)

            for remna_username in usernames:
                sub_name = await remna.update_user(
                    username=remna_username,
                    month=int(month),
                    days=bonus_days,
                    traffic=config.subscription.base_traffic,
                    device_limit=config.subscription.base_devices
                )
                await database.notifications.create_or_update(username=remna_username, notify_days=None)
                
                text = f"Подписка {sub_name} продлена на {month} месяц{suffix[month]}!"
                logger.info(text)
            
            for_log_text = f'продление подписки {sub_name}'

            if not one:
                text = f"Ваши подписки продлены на {month} месяц{suffix[month]}!"
                emoji = '<tg-emoji emoji-id="5280962371207077415">💎</tg-emoji>'
                for_log_text = f'продление {sub_count} подписок'

        await send_to_user(
            bot=bot,
            user=user_id,
            text=text, 
            kb=kb
        )
        
        await database.users.activate_sub(user_id)

        a_link = f'<a href="tg://user?id={user_id}">' if username.isdigit() else f'<a href="tg://resolve?domain={username}">'

        log_text = f'{emoji} Пользователь {a_link}<b>{username}</b></a> оплатил {for_log_text} на {month} месяц{suffix[month]}{add_text}!\n\n'\
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