import os
from aiogram import F
from aiogram import Router
from aiogram.types import CallbackQuery

from service.remna_cmds import remna
from service.nalog import create_simple_receipt

router = Router()


@router.callback_query(F.data == 'admin_menu')
async def admin_menu(callback: CallbackQuery):
    await callback.answer(cache_time=1)

    #kb = InlineKeyboardMarkup(inline_keyboard=[
    #    [InlineKeyboardButton(text='')]
    #await create_simple_receipt(1, "test")

    await callback.message.edit_caption(
        caption='<b>— — Админ панель — —</b>\n\n\n<i>Выберите действие кнопками ниже</i>',
        parse_mode='HTML'
    )