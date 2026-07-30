import logging
from aiogram import F, Router
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import CallbackQuery

from config import config
from handlers.misc import day_word, errors_loging
from database.db import database


logger = logging.getLogger(__name__)
router = Router()
ref_bonus_days = config.subscription.ref_bonus_days

# Основное меню реферальной системы
@router.callback_query(F.data == 'ref_system')
@errors_loging
async def proxy(callback: CallbackQuery):
    await callback.answer(cache_time=1)
    builder = InlineKeyboardBuilder()

    if await database.users.has_payed_sub(callback.from_user.id):
        builder.button(
            text='Моя ссылка', 
            callback_data='ref_stats', 
            icon_custom_emoji_id='5260730055880876557',
            style='success'
        )
    builder.button(
        text='Как пользоваться?',
        callback_data='ref_manual',
        icon_custom_emoji_id='5258474669769497337',
        style='primary'
    )
    builder.button(
        text='В меню', 
        callback_data='menu', 
        icon_custom_emoji_id='5257963315258204021'
    )

    await callback.message.edit_caption(
        caption='<i>Выберите действие кнопками ниже</i>',
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )


# мануал по реферальной системе
@router.callback_query(F.data == 'ref_manual')
@errors_loging
async def ref_manual(callback: CallbackQuery):
    await callback.answer(cache_time=1)

    builder = InlineKeyboardBuilder()
    if await database.users.has_payed_sub(callback.from_user.id):
        builder.button(
            text='Моя ссылка', 
            callback_data='ref_stats', 
            icon_custom_emoji_id='5260730055880876557',
            style='success'
        )
    builder.button(
        text='Назад', 
        callback_data='ref_system',
        icon_custom_emoji_id='5258236805890710909'
    )
    
    await callback.message.edit_caption(
        caption='<tg-emoji emoji-id="5323761960829862762">✨</tg-emoji> За <b>первую</b> покупку каждого приглашённого вами пользователя <b>вы</b> и <b>новый пользователь</b> ' 
        f'получите по <b>{ref_bonus_days} {day_word(days=ref_bonus_days, iskl=True)}</b> к вашим подпискам\n\n'
        '<tg-emoji emoji-id="5258474669769497337">❗️</tg-emoji> Для получения бонуса за приглашённых людей, вам необходимо иметь платную подписку!\n\n'
        '<tg-emoji emoji-id="5258073068852485953">🔗</tg-emoji> Свою ссылку вы можете найти по кнопке ниже.'
        'В том же разделе есть статистика по приглашённым пользователям и бонусным дням',
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )


@router.callback_query(F.data == 'ref_stats')
@errors_loging
async def ref_stats(callback: CallbackQuery, bot_info):
    await callback.answer(cache_time=1)
    user = await database.users.get_user(callback.from_user.id)

    ref_url = f'https://t.me/{bot_info.username}?start={user["referral_code"]}'
    ref_count = int(user["referral_count"])
    bonus_days = ref_bonus_days * ref_count

    builder = InlineKeyboardBuilder()
    builder.button(
        text='Назад',
        callback_data='ref_system',
        icon_custom_emoji_id='5258236805890710909'
    )

    await callback.message.edit_caption(
        caption=f'<tg-emoji emoji-id="5260730055880876557">📎</tg-emoji> <b>Ваша ссылка:</b> <code>{ref_url}</code> <i>(нажмите, чтобы скопировать)</i>\n\n'
        f'<tg-emoji emoji-id="5258513401784573443">👤</tg-emoji> Количество приведённых вами пользователей: {ref_count}\n'
        f'<tg-emoji emoji-id="5258108352008823107">✨</tg-emoji> Суммарное количество бонусных дней: {bonus_days}\n\n'
        f'<i>За каждого приведённого человека вы получите по <b>{ref_bonus_days} {day_word(ref_bonus_days)}</b> ко всем вашим подпискам!</i>',
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )