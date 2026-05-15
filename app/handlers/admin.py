import os
from aiogram import F
from aiogram import Router
from aiogram.types import CallbackQuery

from service.remna_cmds import has_user_sub

router = Router()


@router.callback_query(F.data == 'admin_menu')
async def admin_menu(callback: CallbackQuery):
    await callback.answer()

    #kb = InlineKeyboardMarkup(inline_keyboard=[
    #    [InlineKeyboardButton(text='')]

    await callback.message.edit_caption(caption='<b>— — Админ панель — —</b>\n\n\n<i>Выберите действие кнопками ниже</i>',
                                        parse_mode='HTML')