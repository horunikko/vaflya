import logging
from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import tg_config

logger = logging.getLogger(__name__)
router = Router()

# вы можете поменять инструкцию или текст с информацией.
# для форматирования используйте доступные html теги по ссылке (для незнающих): https://www.misterchatter.com/docs/telegram-html-formatting-guide-supported-tags/
# также вы можете использовать премиум эмодзи с помощью тега <tg-emoji>. этот тег заменяет эмодзи между
# этими тегами на премиум эмодзи. узнать emoji_id можно отправив нужное эмодзи боту @get_emoji_id_robot
# в случае, если у вас нет премиума, будут выводиться дефолтные эмодзи, которые вы подставите для замены
# для переноса строки в текстовом редакторе используйте символ \ (например для удобства записи)
instruction = {
    "android": '<tg-emoji emoji-id="5258336354642697821">⏬</tg-emoji> Откройте страницу приложения <a href="https://play.google.com/store/apps/details?id=llc.itdev.incy">INCY в Google Play</a> и установите его\n\n'\
               '<tg-emoji emoji-id="5258108352008823107">➕</tg-emoji> В разделе "Мои подписки" скопируйте ссылку, затем откройте INCY и в нём нажмите кнопку "Вставить"\n\n'\
               '<tg-emoji emoji-id="5260726538302660868">✅</tg-emoji> Нажмите на большую кнопку включения в центре для подключения к VPN. При необходимости выберите другой сервер из списка серверов (по умолчанию стоит автовыбор)',
    
    "ios": '<tg-emoji emoji-id="5258336354642697821">⏬</tg-emoji> Откройте страницу приложения <a href="https://apps.apple.com/us/app/incy/id6756943388">INCY в App Store</a> и установите его\n\n'\
           '<tg-emoji emoji-id="5258108352008823107">➕</tg-emoji> В разделе "Мои подписки" скопируйте ссылку, затем откройте INCY и в нём нажмите кнопку "Вставить"\n\n'\
           '<tg-emoji emoji-id="5260726538302660868">✅</tg-emoji> Нажмите на большую кнопку включения в центре для подключения к VPN. При необходимости выберите другой сервер из списка серверов (по умолчанию стоит автовыбор)',
    
    "windows": '<tg-emoji emoji-id="5258336354642697821">⏬</tg-emoji> Скачайте приложение <a href="https://github.com/pluralplay/FlClashX/releases/latest/download/FlClashX-windows-amd64-setup.exe">FlClashX по ссылке</a> <i>(текст кликабельный)</i>\n\n'\
               '<tg-emoji emoji-id="5258108352008823107">➕</tg-emoji> В разделе "Мои подписки" скопируйте ссылку, после откройте FlClashX, нажмите кнопку "Добавить профиль" -> "Вставить" -> "Отправить"\n\n'\
               '<tg-emoji emoji-id="5260726538302660868">✅</tg-emoji> Нажмите на большую кнопку включения внизу для подключения к VPN. Если у вас не работают какие-либо сервисы, попробуйте включить системный прокси, либо перезагрузить компьютер'
}

info_text = '<tg-emoji emoji-id="5258508428212445001">💻</tg-emoji> До 5 устройств в подписке\n'\
            '<tg-emoji emoji-id="5323761960829862762">🚀</tg-emoji> Неограниченный трафик\n'\
            '<tg-emoji emoji-id="5260221883940347555">⏫</tg-emoji> Скорость до 1 ГБит/с\n'\
            '<tg-emoji emoji-id="5258077307985207053">⛔️</tg-emoji> Ютуб без рекламы\n'\
            '<tg-emoji emoji-id="5258057130228849960">🌎</tg-emoji> Локации: '\
            '<tg-emoji emoji-id="6320817337033295141">🇩🇪</tg-emoji> Германия, '\
            '<tg-emoji emoji-id="6323216772052813661">🇫🇮</tg-emoji> Финляндия, '\
            '<tg-emoji emoji-id="6323602387101550101">🇵🇱</tg-emoji> Польша'\


def to_tg_link(value: str) -> str:
    """Возвращает значение юзернейма/ссылки в качестве изначальной ссылки, либо ссылки на тг"""
    if value.startswith('https://'):
        return value
    return f'https://t.me/{value.removeprefix("@")}'


support_link = to_tg_link(tg_config.support_link)
channel_link = to_tg_link(tg_config.channel_link)
tg_info = tg_config.info_active
tg_instruction = tg_config.instruction_active


info_buttons = []
if tg_instruction:
    info_buttons.append(InlineKeyboardButton(text='Инструкция', callback_data='manual', style='primary', icon_custom_emoji_id='5258328383183396223'))
if tg_info:
    info_buttons.append(InlineKeyboardButton(text='О тарифе', callback_data='info', style='primary', icon_custom_emoji_id='5258503720928288433'))


info_menu_buttons = [info_buttons] + [
    [
        InlineKeyboardButton(text='Поддержка', url=support_link, icon_custom_emoji_id='5316727448644103237', style='success'),
        InlineKeyboardButton(text='ТГ канал', url=channel_link, icon_custom_emoji_id='5260268501515377807', style='danger')
    ],
    [
        InlineKeyboardButton(text='В меню', callback_data='menu', icon_custom_emoji_id='5257963315258204021')
    ]
]

# используется в функции info_menu
info_menu_kb = InlineKeyboardMarkup(inline_keyboard=info_menu_buttons)

# кнопка Информация в главном меню
@router.callback_query(F.data == 'info_menu')
async def info_menu(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_caption(caption='<b>— — Информация — —</b>\n\n\n'
                                                '<i>Выберите действие кнопками ниже</i>',
                                                parse_mode='HTML',
                                                reply_markup=info_menu_kb)


# ведёт в меню с информацией
manual_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Android', callback_data='manual_android', icon_custom_emoji_id='5174698235989590607')],
    [InlineKeyboardButton(text='IOS (Apple)', callback_data='manual_ios', icon_custom_emoji_id='5175018305542423078')],
    [InlineKeyboardButton(text='Windows', callback_data='manual_windows', icon_custom_emoji_id='5174885865930883798')],
    [InlineKeyboardButton(text='Назад', callback_data='info_menu', icon_custom_emoji_id='5258236805890710909')]
])

# кнопка Инструкция
@router.callback_query(F.data == 'manual')
async def manual(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_caption(caption='<b>— — Инструкция — —</b>\n\n\nВыберите ваше устройство:',
                                        parse_mode='HTML', reply_markup=manual_kb)


# сама по себе инструкция
@router.callback_query(F.data.startswith('manual_'))
async def manual_android(callback: CallbackQuery):
    device = callback.data.removeprefix('manual_')
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Мои подписки', callback_data='get_subs', icon_custom_emoji_id='5226513232549664618', style='success')],
        [InlineKeyboardButton(text='Назад', callback_data='manual', icon_custom_emoji_id='5258236805890710909')]
    ])

    await callback.answer()
    await callback.message.edit_caption(caption=f'<b>— — Инструкция — —</b>\n\n{instruction[device]}',
                                        parse_mode='HTML',
                                        reply_markup=kb)


# кнопка О тарифе
@router.callback_query(F.data == 'info')
async def info(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='info_menu', icon_custom_emoji_id='5258236805890710909')]
    ])
    await callback.answer()
    await callback.message.edit_caption(caption=f'<b>— — О подписке — —</b>\n\n\n{info_text}',
                                                parse_mode='HTML',
                                                reply_markup=kb)