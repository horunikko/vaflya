import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import config
from handlers.misc import instruction, errors_loging, info_kb, read_file, info_text

logger = logging.getLogger(__name__)
router = Router()


def create_manual_kb(instruction: dict) -> InlineKeyboardMarkup:
    """Формируем клавиатуру по наличию файлов"""
    builder = InlineKeyboardBuilder()

    labels = {
        "android": ("Android", "manual_android", "5174698235989590607", 'success'),
        "ios": ("IOS", "manual_ios", "5175018305542423078", 'primary'),
        "windows": ("Windows", "manual_windows", "5174885865930883798", 'primary'),
        "linux": ("Linux", "manual_linux", "5307512248418182650", 'primary')
    }

    for device, value in instruction.items():
        if value:
            device_text, callback, emoji, style = labels[device]
            builder.button(
                text=device_text, 
                callback_data=callback, 
                icon_custom_emoji_id=emoji,
                style=style
            )
    builder.button(
        text='Назад', 
        callback_data='info_menu', 
        icon_custom_emoji_id='5258236805890710909'
    )

    return builder.adjust(1).as_markup()


manual_kb = create_manual_kb(instruction)


# кнопка Информация в главном меню
@router.callback_query(F.data == 'info_menu')
@errors_loging
async def info_menu(callback: CallbackQuery):
    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption='<i>Выберите действие кнопками ниже</i>',
        parse_mode='HTML',
        reply_markup=info_kb
    )


# кнопка Инструкция
@router.callback_query(F.data == 'manual')
@errors_loging
async def manual(callback: CallbackQuery):
        await callback.answer(cache_time=1)
        await callback.message.edit_caption(
            caption='<i>Выберите ваше устройство:</i>',
            parse_mode='HTML',
            reply_markup=manual_kb
        )


# сама по себе инструкция
@router.callback_query(F.data.startswith('manual_'))
@errors_loging
async def manual_android(callback: CallbackQuery):
    device = callback.data.removeprefix('manual_')

    builder = InlineKeyboardBuilder()
    builder.button(
        text='Мои подписки', 
        callback_data='get_subs', 
        icon_custom_emoji_id='5226513232549664618', 
        style='success'
    )
    builder.button(
        text='Назад', 
        callback_data='manual', 
        icon_custom_emoji_id='5258236805890710909'
    )

    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption=instruction[device],
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )


# кнопка О тарифе
@router.callback_query(F.data == 'info')
@errors_loging
async def info(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Назад', 
        callback_data='info_menu', 
        icon_custom_emoji_id='5258236805890710909'
    )
    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption=info_text,
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )