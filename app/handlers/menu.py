import asyncio
import logging

from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, CommandObject
from aiogram.exceptions import TelegramForbiddenError
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.formatting import TextMention, Text

from handlers.misc import inline_start, day_word, get_random_photo, errors_loging
from service.remna import remna

from database.db import database
from config import config


logger = logging.getLogger(__name__)
router = Router()


async def push(bot: Bot) -> None:
    """Каждый час пытается выслать уведомление пользователю об окончании подписки"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Мои подписки', 
        callback_data='get_subs', 
        icon_custom_emoji_id='5226513232549664618',
        style='success'
    )
    await asyncio.sleep(600)
    while True:
        for day in config.telegram.notify_days:
            users = await remna.expire_day(days=day)
            for user in users:
                try:
                    await bot.send_photo(
                        chat_id=user,
                        photo=FSInputFile(get_random_photo()),
                        caption='<b>— — Уведомление — —</b>\n\n\n'
                        f'Ваша подписка заканчивается через {day} {day_word(day)}! Не забудьте продлить её!',
                        reply_markup=builder.adjust(1).as_markup(),
                        parse_mode='HTML'
                    )
                    logger.info(f"Пользователь {user} уведомлён")

                except TelegramForbiddenError:
                    logger.info(f"Пользователь {user} заблокировал бота")
                    continue

                except Exception:
                    logger.exception(f"Непредвиденная ошибка")
                    continue

                await asyncio.sleep(0.05)
            
        await asyncio.sleep(3600)


# менюшка командная
@router.message(CommandStart())
@errors_loging
async def get_start(message: Message, command: CommandObject, bot_info):
    ref_code = command.args
    tg_id = message.from_user.id
    ref_from = None
    has_payed_sub = None

    caption = f'<b>— — Вас приветствует {bot_info.first_name} ! — —</b>\n\n\n<i>Выберите действие кнопками ниже</i>'

    if ref_code:
        if not config.subscription.ref_bonus_days:
            await message.answer(
                text="<b>— — Рефералка — —</b>\n\n\n"
                '<tg-emoji emoji-id="5260412365739925015">🚫</tg-emoji> '
                "Реферальная система отключена.",
                parse_mode='HTML'
            )
        if await database.users.has_payed_sub(tg_id):
            await message.answer(
                text="<b>— — Рефералка — —</b>\n\n\n"
                '<tg-emoji emoji-id="5260412365739925015">🚫</tg-emoji> '
                "У вас уже есть платная подписка, вы не можете использовать чужие реферальный ссылки, но можете поделиться своей для получения бонуса!",
                parse_mode='HTML'
            )
        else:
            ref_from: int | None = await database.users.referral_from_by_ref_code(ref_code)
            if not ref_from:
                await message.answer(
                    text="<b>— — Рефералка — —</b>\n\n\n"
                    '<tg-emoji emoji-id="5275969776668134187">❗️</tg-emoji> '
                    "Не найден реферальный код. Убедитесь в правильности реферальной ссылки",
                    parse_mode='HTML'
                )
            elif ref_from == tg_id:
                await message.answer(
                    text="<b>— — Рефералка — —</b>\n\n\n"
                    '<tg-emoji emoji-id="5258362429389152256">❌</tg-emoji> '
                    "Вы не можете использовать свою рефералку, не хитрите!",
                    parse_mode='HTML'
                )
                ref_from = None
            else:
                user = await database.users.get_username(ref_from) or ref_from
                await message.answer(
                    text="<b>— — Рефералка — —</b>\n\n\n"
                    '<tg-emoji emoji-id="5260726538302660868">✅</tg-emoji> '
                    f"Реферальная ссылка от пользователя {user} активирована! После оплаты вы получите дополнительных {config.subscription.ref_bonus_days} {day_word(config.subscription.ref_bonus_days)}!",
                    parse_mode='HTML'
                )
        await asyncio.sleep(2.5)

    if not await database.users.get_user(tg_id) and await remna.has_user_sub(tg_id):
        has_payed_sub = 1

    await database.users.create(
        tg_id=tg_id, 
        username=message.from_user.username.lower() if message.from_user.username else None,
        referral_from=ref_from,
        has_user_sub=has_payed_sub
    )

    await message.answer_photo(
        photo=FSInputFile(get_random_photo()),
        caption=caption,
        parse_mode='HTML',
        reply_markup=inline_start(message.from_user.id)
    )

# менюшка. для вызова из под кнопок "меню" и "назад"
@router.callback_query(F.data == 'menu')
@errors_loging
async def cb_menu(callback: CallbackQuery, bot_info):
    tg_id = callback.from_user.id
    has_payed_sub = None

    if not await database.users.get_user(tg_id) and await remna.has_user_sub(tg_id):
        has_payed_sub = 1
    
    await database.users.create(
        tg_id=callback.from_user.id,
        username=callback.from_user.username.lower() if callback.from_user.username else None,
        has_user_sub=has_payed_sub
    )

    caption = f'<b>— — Вас приветствует {bot_info.first_name} ! — —</b>\n\n\n<i>Выберите действие кнопками ниже</i>'

    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption=caption,
        parse_mode='HTML',
        reply_markup=inline_start(callback.from_user.id)
    )