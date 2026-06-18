import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import config
from handlers.misc import instruction, errors_loging, read_file

logger = logging.getLogger(__name__)
router = Router()

info_text = read_file("app/texts/info.txt")

kb_builder = InlineKeyboardBuilder()

if any(instruction.values()):
    kb_builder.button(
        text='Как подключить?',
        callback_data='manual',
        style='primary', 
        icon_custom_emoji_id='5258328383183396223'
    )
else:
    logger.info("Кнопка 'Как подключить?' отключена")
if info_text:
    kb_builder.button(
        text='О тарифе',
        callback_data='info', 
        style='primary', 
        icon_custom_emoji_id='5258503720928288433'
    )
else:
    logger.info("Кнопка 'О тарифе' отключена")
if config.telegram.support_link:
    kb_builder.button(
        text='Поддержка',
        url=config.telegram.support_link,
        icon_custom_emoji_id='5316727448644103237',
        style='success'
    ),
else:
    logger.info("Кнопка 'Поддержка' отключена")
if config.telegram.channel_link:
    kb_builder.button(
        text='ТГ канал', 
        url=config.telegram.channel_link, 
        icon_custom_emoji_id='5260268501515377807', 
        style='danger'
    )
else:
    logger.info("Кнопка 'ТГ канал' отключена")
kb_builder.button(
    text='В меню', 
    callback_data='menu', 
    icon_custom_emoji_id='5257963315258204021'
)


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
        caption='<b>— — Информация — —</b>\n\n\n<i>Выберите действие кнопками ниже</i>',
        parse_mode='HTML',
        reply_markup=kb_builder.adjust(2).as_markup()
    )


# кнопка Инструкция
@router.callback_query(F.data == 'manual')
@errors_loging
async def manual(callback: CallbackQuery):
    for _ in range(3):
        try:
            await callback.answer(cache_time=1)
            await callback.message.edit_caption(
                caption='<b>— — Инструкция — —</b>\n\n\nВыберите ваше устройство:',
                parse_mode='HTML',
                reply_markup=manual_kb
            )
            break
        except TelegramBadRequest:
            pass


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
        caption=f'<b>— — Инструкция — —</b>\n\n{instruction[device]}',
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
        caption=f'<b>— — О тарифе — —</b>\n\n\n{info_text}',
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )