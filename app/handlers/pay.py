import os
import logging
from config import pay_config, nalogo_config
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton
from service.nalog import create_simple_receipt
from service.remna_cmds import remna_create_user, update_user

logger = logging.getLogger(__name__)
router = Router()


YOOKASSA_TOKEN = pay_config.yookassa_token
NALOGO_ACTIVE = nalogo_config.active
ONE_MONTH = pay_config.one_month
THREE_MONTHS = pay_config.three_month
ONE_YEAR = pay_config.one_year
 

# кнопочка для выхода в менюшку после оплаты
pay_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Инструкция', callback_data='manual', style='primary', icon_custom_emoji_id='5258328383183396223')],
    [InlineKeyboardButton(text='В меню', callback_data='pay_menu', icon_custom_emoji_id='5257963315258204021')]
])
suffix = {"1": "", "3": "а", "12": "ев"}


# создание платежа
@router.callback_query(F.data.startswith('upay_'))
async def upay(callback: CallbackQuery):
    month = callback.data.removeprefix('upay_')
    uuid = ''

    if '_' in month:
        uuid = month.split("_")[0]
        month = month.split("_")[1]
    
    price_list = {"1": ONE_MONTH, "3": THREE_MONTHS, "12": ONE_YEAR}

    prices = [
        LabeledPrice(
            label=f"Подписка на {month} месяц{suffix[month]}",
            amount=(int(price_list[month]) * 100)
        )
    ]

    await callback.answer()
    await callback.message.answer_invoice(
        title='— — Оплата — —',
        description=f'{"Продление подписки" if uuid else "Подписка"} на {month} месяц{suffix[month]}. '
                    f'После оплаты {"подписка продлится автоматически"if uuid else "вам будет выдана подписка"} на выбранный срок. '
                    'Если у вас не загружается оплата, попробуйте снова через несколько минут, проблема на стороне платёжной системы.',
        payload=f"vpn_{f"{uuid}_" if uuid else ''}{month}",
        provider_token=YOOKASSA_TOKEN,
        currency="RUB",
        prices=prices
    )


# подтверждение платежа
@router.pre_checkout_query()
async def pre_ch(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


# успешная оплата платежа
@router.message(F.successful_payment)
async def successful_payment(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else str(user_id)
    month = message.successful_payment.invoice_payload.removeprefix("vpn_")

    uuid = ''

    if '_' in month:
        uuid = month.split("_")[0]
        month = month.split("_")[1]

    logger.info(f"Пользователь {username} купил {"подписку" if not uuid else "продление подписки"} на {month} месяц{suffix[month]}")

    try:
        if not uuid:
            sub = await remna_create_user(username, str(user_id), int(month))
            text = f"Ваша подписка на {month} месяц{suffix[month]}:\n\n{sub}"
            logger.info(f"Подписка успешно выдана")
        else:
            sub_name = await update_user(uuid, int(month))
            text = f"Подписка {sub_name} продлена на {month} месяц{suffix[month]}!"
            logger.info(f"Подписка была успешно продлена")

        await message.answer(text=f"<b>— — Оплата прошла успешно! — —</b>\n\n\n{text}",
                                    parse_mode='HTML',
                                    reply_markup=pay_menu)
    except Exception as e:
        logger.exception(f"Произошла ошибка при оплате")
        await message.answer(text='Произошла непредвиденная ошибка! Просьба обратиться в поддержку (личные сообщения канала @horuvpn) для получения/продления '
                             'подписки с учётом компенсации!')

    if NALOGO_ACTIVE:
        receipt = await create_simple_receipt(month=month, user=str(user_id))