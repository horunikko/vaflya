import logging
from aiogram import F, Router
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import CallbackQuery

from config import sub_config
from handlers.keyboards import day_word
from database.db import database


logger = logging.getLogger(__name__)
router = Router()
ref_bonus_days = sub_config.ref_bonus_days

# Основное меню реферальной системы
@router.callback_query(F.data == 'ref_system')
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
        caption='<b>— — Реферальная система — —</b>\n\n\n'
        '<i>Выберите действие кнопками ниже</i>',
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )


# мануал по реферальной системе
@router.callback_query(F.data == 'ref_manual')
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
        caption='<b>— — Реферальная система — —</b>\n\n\n'
        '<tg-emoji emoji-id="5323761960829862762">✨</tg-emoji> За первую покупку каждого приглашённого вами пользователя вы и новый пользователь ' 
        f'получите по {ref_bonus_days} {day_word(days=ref_bonus_days, iskl=True)} к вашим подпискам\n\n'
        '<tg-emoji emoji-id="5258073068852485953">🔗</tg-emoji> Чтобы иметь возможность приглашать других людей и получать бонус вам необходимо иметь '
        'платную подписку. После того, как у вас появится платная подписка, вы можете скопировать свою ссылку по кнопкам <b>Реферальная система</b> → <b>Моя ссылка</b>. '
        'В том же разделе вы сможете посмотреть статистику по приглашённым пользователям и бонусным дням',
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )


@router.callback_query(F.data == 'ref_stats')
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
        caption='<b>— — Рефералка — —</b>\n\n\n'
        f'<tg-emoji emoji-id="5260730055880876557">📎</tg-emoji> Ваша реферальная ссылка: <code>{ref_url}</code> <i>(кликабельно)</i>\n\n'
        f'Количество приведённых вами пользователей: {ref_count}\n'
        f'Количество бонусных дней: {bonus_days}',
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )