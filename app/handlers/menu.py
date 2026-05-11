import os
import random
import asyncio
from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from handlers.keyboards import inline_start
from service.remna_cmds import expire_day

router = Router()
kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Мои подписки', callback_data='get_subs', icon_custom_emoji_id='5226513232549664618')]])


def get_random_photo() -> str:
    """Возвращает путь случайного файла из папки photos"""
    files = [photo for photo in os.listdir("app/menu_photos")]

    file = random.choice(files)
    return os.path.join("app/menu_photos", file)


async def push(bot: Bot):
    while True:
        users = await expire_day(1)
        for user in users:
            try:
                await bot.send_photo(chat_id=user,
                                    photo=FSInputFile(get_random_photo()),
                                    caption='<b>— — Уведомление — —</b>\n\n\n'
                                    'Ваша подписка заканчивается через 1 день! Не забудьте продлить её!',
                                    reply_markup=kb,
                                    parse_mode='HTML')
            except Exception as e:
                print("похуй проебали (пользователь заблокал бота)")
            await asyncio.sleep(0.05)
            
        await asyncio.sleep(3600)

def caption(bot_info) -> str:
    """Выводит текст главного меню"""
    return f'<b>— — Вас приветствует {bot_info.first_name} ! — —</b>\n\n\n<i>Выберите действие кнопками ниже</i>'

# менюшка командная
@router.message(CommandStart())
async def get_start(message: Message, bot_info):
    await message.answer_photo(photo=FSInputFile(get_random_photo()),
                               caption=caption(bot_info),
                               parse_mode='HTML', reply_markup=inline_start(message.from_user.id))

# менюшка. для вызова из под кнопок "меню" и "назад"
@router.callback_query(F.data == 'menu')
async def cb_menu(callback: CallbackQuery, bot_info):
    await callback.answer()
    await callback.message.edit_caption(caption=caption(bot_info),
                                        parse_mode='HTML',
                                        reply_markup=inline_start(callback.from_user.id))


# вызов менюшки после оплаты
@router.callback_query(F.data == 'pay_menu')
async def payMenu(callback: CallbackQuery, bot_info):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer_photo(photo=FSInputFile(get_random_photo()),
                                        caption=caption(bot_info),
                                        parse_mode='HTML', reply_markup=inline_start(callback.from_user.id))