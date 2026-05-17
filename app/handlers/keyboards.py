import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import tg_config
from handlers.info import instruction


logger = logging.getLogger(__name__)

admin_list = tg_config.admin_ids

if admin_list:
    admin_list = admin_list.split(",")


def inline_start(user_id: str | int = None) -> InlineKeyboardMarkup:
    """Возвращает клавиатуру на странице главного меню"""
    builder = InlineKeyboardBuilder()

    builder.button(
        text='Подписки', 
        callback_data='subs', 
        style='success', 
        icon_custom_emoji_id="5226513232549664618"
    )
    builder.button(
        text='Информация', 
        callback_data='info_menu', 
        style='primary', 
        icon_custom_emoji_id='5258503720928288433'
    )

    if str(user_id) in admin_list:
        builder.button(
            text='Админ панель', 
            callback_data='admin_menu', 
            style='danger', 
            icon_custom_emoji_id='5258096772776991776'
        )
        
    return builder.adjust(1).as_markup()


def choose_action(uuid, one=True) -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру с выбором Продлить/Устройства/Назад.
    Вызывается только с выводом информации о подписке пользователя.
    Значение one (количество подписок) определяет, вернётся ли пользователь
    в главное меню, либо в меню выбора подписок 
    """
    buttons = [
        [
            InlineKeyboardButton(
                text='Продлить', 
                callback_data=f'month_{uuid}', 
                style='success', 
                icon_custom_emoji_id='5260687119092817530'
            )
        ],
        [
            InlineKeyboardButton(
                text='Устройства', 
                callback_data=f'device_{uuid}', 
                style='primary', 
                icon_custom_emoji_id='5258508428212445001'
            )
        ]
    ]
    
    if instruction:
        buttons.append(
            [
                InlineKeyboardButton(
                    text='Инструкция', 
                    callback_data='manual', 
                    style='primary', 
                    icon_custom_emoji_id='5258328383183396223'
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text='Назад', 
                callback_data=f'{'subs' if one else 'get_subs'}', 
                icon_custom_emoji_id='5258236805890710909'
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)