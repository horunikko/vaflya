from pydantic import BaseModel
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text='Инструкция', 
            callback_data='manual', 
            style='success', 
            icon_custom_emoji_id='5258328383183396223'
        )
    ],
    [
        InlineKeyboardButton(
            text='Подписки', 
            callback_data='subs', 
            style='primary', 
            icon_custom_emoji_id="5226513232549664618"
        )
    ],
    [
        InlineKeyboardButton(
            text='В меню', 
            callback_data='menu', 
            icon_custom_emoji_id='5257963315258204021'
        )
    ]
])

ref_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text='Подписки', 
            callback_data='subs', 
            style='success', 
            icon_custom_emoji_id="5226513232549664618"
        )
    ],
    [
        InlineKeyboardButton(
            text='Реферальная система',
            callback_data='ref_system',
            style='primary',
            icon_custom_emoji_id='5258165702707125574'
        )
    ],
    [
        InlineKeyboardButton(
            text='В меню', 
            callback_data='menu', 
            icon_custom_emoji_id='5257963315258204021'
        )
    ]
])


class Amount(BaseModel):
    value: float
    currency: str


class Metadata(BaseModel):
    remna_username: str | None
    month: int
    user_id: int
    username: str


class WebhookObject(BaseModel):
    id: str
    status: str
    amount: Amount
    income_amount: Amount
    captured_at: str
    created_at: str
    test: bool
    refunded_amount: Amount
    paid: bool
    refundable: bool
    metadata: Metadata


class WebhookData(BaseModel):
    type: str
    event: str
    object: WebhookObject