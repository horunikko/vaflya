import logging
from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import tg_config

logger = logging.getLogger(__name__)
router = Router()


def read_file(file: str) -> str | None:
    """Функция чтения файла"""
    try:
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()

            if not text.strip():
                logger.info(f"Файл {file} пуст, не используем его")
                return None
            
            return text
        
    except FileNotFoundError:
        logger.info(f"Отсутствует файл {file}")
        return None


info_text = read_file("app/texts/info.txt")
instruction = {
    "android": read_file("app/texts/instruction_android.txt"),
    "ios": read_file("app/texts/instruction_ios.txt"),
    "windows": read_file("app/texts/instruction_windows.txt"),
    "linux": read_file("app/texts/instruction_linux.txt")
}


def to_tg_link(value: str) -> str:
    """Возвращает значение юзернейма/ссылки в качестве изначальной ссылки, либо ссылки на тг"""
    if value.startswith('https://'):
        return value
    return f'https://t.me/{value.removeprefix("@")}'


support_link = to_tg_link(tg_config.support_link)
channel_link = to_tg_link(tg_config.channel_link)


info_buttons = []

if any(instruction.values()):
    info_buttons.append(InlineKeyboardButton(
        text='Как подключить?',
        callback_data='manual',
        style='primary', 
        icon_custom_emoji_id='5258328383183396223'))
else:
    logger.info("Кнопка 'Инструкция' отключена")


if info_text:
    info_buttons.append(InlineKeyboardButton(
        text='О тарифе', 
        callback_data='info', 
        style='primary', 
        icon_custom_emoji_id='5258503720928288433'))
else:
    logger.info("Кнопка 'О тарифе' отключена")


info_menu_buttons = [info_buttons] + [
    [
        InlineKeyboardButton(
            text='Поддержка', 
            url=support_link, 
            icon_custom_emoji_id='5316727448644103237', 
            style='success'), 
        InlineKeyboardButton(
            text='ТГ канал', 
            url=channel_link, 
            icon_custom_emoji_id='5260268501515377807', 
            style='danger')
    ],
    [
        InlineKeyboardButton(
            text='В меню', 
            callback_data='menu', 
            icon_custom_emoji_id='5257963315258204021')
    ]
]


def create_manual_kb(instruction: dict) -> InlineKeyboardMarkup:
    """Формируем клавиатуру по наличию файлов"""
    buttons = []

    labels = {
        "android": ("Android", "manual_android", "5174698235989590607", 'success'),
        "ios": ("IOS", "manual_ios", "5175018305542423078", 'primary'),
        "windows": ("Windows", "manual_windows", "5174885865930883798", 'primary'),
        "linux": ("Linux", "manual_linux", "5307512248418182650", 'primary')
    }

    for device, value in instruction.items():
        if value:
            device_text, callback, emoji, style = labels[device]
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=device_text, 
                        callback_data=callback, 
                        icon_custom_emoji_id=emoji,
                        style=style
                    )
                ]
            )
    
    buttons.append(
        [
            InlineKeyboardButton(
                text='Назад', 
                callback_data='info_menu', 
                icon_custom_emoji_id='5258236805890710909'
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


info_menu_kb = InlineKeyboardMarkup(inline_keyboard=info_menu_buttons)
manual_kb = create_manual_kb(instruction)


# кнопка Информация в главном меню
@router.callback_query(F.data == 'info_menu')
async def info_menu(callback: CallbackQuery):
    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption='<b>— — Информация — —</b>\n\n\n<i>Выберите действие кнопками ниже</i>',
        parse_mode='HTML',
        reply_markup=info_menu_kb
    )


# кнопка Инструкция
@router.callback_query(F.data == 'manual')
async def manual(callback: CallbackQuery):
    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption='<b>— — Инструкция — —</b>\n\n\nВыберите ваше устройство:',
        parse_mode='HTML', 
        reply_markup=manual_kb
    )


# сама по себе инструкция
@router.callback_query(F.data.startswith('manual_'))
async def manual_android(callback: CallbackQuery):
    device = callback.data.removeprefix('manual_')

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text='Мои подписки', 
                callback_data='get_subs', 
                icon_custom_emoji_id='5226513232549664618', 
                style='success'
            )
        ],
        [
            InlineKeyboardButton(
                text='Назад', 
                callback_data='manual', 
                icon_custom_emoji_id='5258236805890710909'
            )
        ]
    ])

    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption=f'<b>— — Инструкция — —</b>\n\n{instruction[device]}',
        parse_mode='HTML',
        reply_markup=kb
    )


# кнопка О тарифе
@router.callback_query(F.data == 'info')
async def info(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text='Назад', 
                callback_data='info_menu', 
                icon_custom_emoji_id='5258236805890710909'
            )
        ]
    ])
    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption=f'<b>— — О тарифе — —</b>\n\n\n{info_text}',
        parse_mode='HTML',
        reply_markup=kb
    )