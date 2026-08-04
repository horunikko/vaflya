import os
import random
import logging
from functools import wraps

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from config import config


logger = logging.getLogger(__name__)


def errors_loging(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):

        try:
            return await func(*args, **kwargs)

        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                return
            else:
                logger.error("Произошла непредвиденная ошибка:", exc_info=True)

        except Exception as e:
            logger.error("Произошла непредвиденная ошибка:", exc_info=True)

    return wrapper


def inline_start(user_id: str | int = None) -> InlineKeyboardMarkup:
    """Возвращает клавиатуру на странице главного меню"""
    builder = InlineKeyboardBuilder()

    builder.button(
        text='Подписки',
        callback_data='subs',
        style='success',
        icon_custom_emoji_id="5226513232549664618"
    )
    if config.subscription.ref_bonus_days:
        builder.button(
            text='Реферальная система',
            callback_data='ref_system',
            style='primary',
            icon_custom_emoji_id='5258165702707125574'
        )
    if info_kb:
        builder.button(
            text='Информация',
            callback_data='info_menu',
            style='danger',
            icon_custom_emoji_id='5258503720928288433'
        )
    if user_id in config.telegram.admin_ids:
        builder.button(
            text='Админ панель',
            callback_data='admin_menu',
            style='danger',
            icon_custom_emoji_id='5258096772776991776'
        )
        
    return builder.adjust(1).as_markup()


def choose_action(uuid: str, one: bool | None = True) -> InlineKeyboardMarkup:

    """Возвращает клавиатуру с выбором Продлить/Устройства/Назад.
    Вызывается только с выводом информации о подписке пользователя.
    Значение one (количество подписок) определяет, вернётся ли пользователь
    в главное меню, либо в меню выбора подписок"""

    builder = InlineKeyboardBuilder()

    x = 1
    builder.button(
        text='Продлить',
        callback_data=f'month_{uuid}',
        style='success',
        icon_custom_emoji_id='5258419835922030550'
    )
    builder.button(
        text='Устройства',
        callback_data=f'device_{uuid}',
        style='primary',
        icon_custom_emoji_id='5258508428212445001'
    )
    if any(instruction.values()):
        x = 2
        builder.button(
            text='Инструкция',
            callback_data='manual',
            style='primary',
            icon_custom_emoji_id='5258328383183396223'
        )
    builder.button(
        text='Назад',
        callback_data=f'{"subs" if one else "get_subs"}',
        icon_custom_emoji_id='5258236805890710909'
    )

    return builder.adjust(1, x).as_markup()


def sub_action(users: dict[str, str], tg_id: int | str, admin: bool | None = False) -> InlineKeyboardMarkup:
    """Возвращает клавиатуру для выбора подписок, с которой пользователь будет взаимодействовать"""
    builder = InlineKeyboardBuilder()

    x = 0
    first = 2
    second = 1

    for username, uuid in users.items():
        x += 1
        builder.button(
            text=username,
            callback_data=f"{'admin_' if admin else ''}sub_action_{str(uuid)}",
            style='primary',
            icon_custom_emoji_id='5260399854500191689'
        )
    builder.button(
        text="Массовые действия" if admin else "Продлить все подписки",
        callback_data=f"admin_mass_actionbs_{tg_id}" if admin else f"month_{x}",
        style='success',
        icon_custom_emoji_id='5258513401784573443'
    )
    builder.button(
        text="Назад",
        callback_data="admin_menu" if admin else "subs",
        icon_custom_emoji_id='5258236805890710909'
    )
    if x > 3:
        second = 2

    return builder.adjust(first, second, 1, 1).as_markup()


async def send_to_user(bot: Bot, user: int | str, text: str, kb: InlineKeyboardMarkup):
    """Функция отправки юзеру сообщения по его айди, тексту и клавиатуре"""
    try:
        await bot.send_photo(
            chat_id=str(user),
            photo=FSInputFile(get_random_photo()),
            caption=text,
            reply_markup=kb,
            parse_mode='HTML'
        )

    except TelegramForbiddenError:
        logger.info(f"Пользователь {user} заблокировал бота")

    except TelegramBadRequest as e:
        if 'chat not found' in str(e):
            logger.info(f"Чат с айди {user} не существует!")
        else:
            logger.exception(f"Непредвиденная ошибка при отправке сообщения пользователю {user}")

    except Exception:
        logger.exception(f"Непредвиденная ошибка при отправке сообщения пользователю {user}")


def day_word(days: int, iskl: bool | None = None) -> str:
    """Возвращает правильное склонение слова 'день'"""

    days = abs(days) % 100
    last = days % 10

    if 11 <= days <= 14:
        return "дней"

    if last == 1:
        if iskl:
            return "дня"
        return "день"

    if 2 <= last <= 4:
        return "дня"

    return "дней"


def get_random_photo() -> str:
    """Возвращает путь случайного файла из папки photos"""
    files = [photo for photo in os.listdir("app/menu_photos")]

    file = random.choice(files)
    return os.path.join("app/menu_photos", file)


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


def if_info(info_text) -> InlineKeyboardMarkup | None:
    """Создание клавиатуры для главного меню"""
    kb_builder = InlineKeyboardBuilder()

    if any(instruction.values()):
        kb_builder.button(
            text='Инструкция',
            callback_data='manual',
            style='primary', 
            icon_custom_emoji_id='5258328383183396223'
        )
    else:
        logger.info("Кнопка 'Инструкция' отключена")

    if info_text:
        kb_builder.button(
            text='О сервисе',
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
        )
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
    
    x = len(list(kb_builder.buttons))

    kb_builder.button(
        text='В меню', 
        callback_data='menu', 
        icon_custom_emoji_id='5257963315258204021'
    )
    if not x:
        return None
    return kb_builder.adjust(int(x//2)).as_markup()


suffix = {
    "1": "",
    "3": "а",
    "6": "ев",
    "12": "ев",
    "24": "а"
}

price_list = {
    "1": config.price.one,
    "3": config.price.three, 
    "6": config.price.six,
    "12": config.price.twelve,
    "24": config.price.twenty_four
}

instruction = {
    "android": read_file("app/texts/instruction_android.txt"),
    "ios": read_file("app/texts/instruction_ios.txt"),
    "windows": read_file("app/texts/instruction_windows.txt"),
    "linux": read_file("app/texts/instruction_linux.txt")
}

info_text = read_file("app/texts/info.txt")
info_kb = if_info(info_text)