import asyncio
import logging

from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.formatting import TextMention, Text
from aiogram.fsm.context import FSMContext

from handlers.misc import inline_start, day_word, get_random_photo, errors_loging, send_to_user
from service.remna import remna

from database.db import database
from config import config


logger = logging.getLogger(__name__)
router = Router()


def push_kb(uuid):
    """Клавиатура для уведомлений"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Продлить подписку',
        callback_data=f'month_{uuid}',
        icon_custom_emoji_id='5258419835922030550',
        style='success'
    )
    kb_builder.button(
        text='В меню', 
        callback_data='menu', 
        icon_custom_emoji_id='5257963315258204021'
    )
    return builder.adjust(1).as_markup()


async def push(bot: Bot) -> None:
    """Каждый час пытается выслать уведомление пользователю об окончании подписки"""
    await asyncio.sleep(100)
    while True:
        grouped_users = await remna.expire_day(notify_days=config.telegram.notify_days, end_notify=config.telegram.sub_end_notify)

        for day, user_info in grouped_users.items():
            for user in user_info:

                if day == 0:
                    text = f'<tg-emoji emoji-id="5258474669769497337">❗️</tg-emoji> Подписка {user["username"]} истекла!\n\nДля продолжения пользования сервисом продлите подписку!'
                else:
                    text = f'<tg-emoji emoji-id="5258258882022612173">⏳</tg-emoji> Подписка {user["username"]} истекает через {day} {day_word(day)}! Не забудьте продлить её!'

                await send_to_user(bot=bot, user=user["user_id"], text=text, kb=push_kb(user["user_uuid"]))

                logger.info(f'Пользователь {user["user_id"]} уведомлён')
                await asyncio.sleep(0.05)
            
        await asyncio.sleep(3600)


# менюшка командная
@router.message(CommandStart())
@errors_loging
async def get_start(message: Message, command: CommandObject, bot_info, state: FSMContext):
    await state.clear()

    ref_code = command.args
    tg_id = message.from_user.id
    ref_from = None
    has_payed_sub = None

    caption = f'<b><tg-emoji emoji-id="5258501105293205250">👏</tg-emoji> Вас приветствует {bot_info.first_name} !</b>\n\n<i>Выберите действие кнопками ниже</i>'

    if ref_code:
        if await database.users.has_payed_sub(tg_id):
            await message.answer(
                text='<tg-emoji emoji-id="5260412365739925015">🚫</tg-emoji> '
                "У вас уже есть платная подписка, для получения бонуса вы можете делиться своей ссылкой!",
                parse_mode='HTML'
            )
        else:
            ref_from: int | None = await database.users.referral_from_by_ref_code(ref_code)
            if not ref_from or ref_from == tg_id:
                await message.answer(
                    text='<tg-emoji emoji-id="5275969776668134187">❗️</tg-emoji> '
                    "Неверный реферальный код\n\nУбедитесь в правильности реферальной ссылки",
                    parse_mode='HTML'
                )
                ref_from = None
            else:
                user = await database.users.get_username(ref_from) or ref_from
                await message.answer(
                    text='<tg-emoji emoji-id="5260726538302660868">✅</tg-emoji> '
                    f"Реферальная ссылка пользователя {user} активирована!\n\n"
                    f"После оплаты вы получите дополнительных {config.subscription.ref_bonus_days} {day_word(config.subscription.ref_bonus_days)}!",
                    parse_mode='HTML'
                )
        await asyncio.sleep(1.5)

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
async def cb_menu(callback: CallbackQuery, bot_info, state: FSMContext):
    await state.clear()

    tg_id = callback.from_user.id
    has_payed_sub = None

    if not await database.users.get_user(tg_id) and await remna.has_user_sub(tg_id):
        has_payed_sub = 1
    
    await database.users.create(
        tg_id=callback.from_user.id,
        username=callback.from_user.username.lower() if callback.from_user.username else None,
        has_user_sub=has_payed_sub
    )

    caption = f'<b><tg-emoji emoji-id="5258501105293205250">👏</tg-emoji> Вас приветствует {bot_info.first_name} !</b>\n\n<i>Выберите действие кнопками ниже</i>'

    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption=caption,
        parse_mode='HTML',
        reply_markup=inline_start(callback.from_user.id)
    )