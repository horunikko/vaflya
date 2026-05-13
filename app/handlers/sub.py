import logging
from aiogram import F, Router
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from service.remna_cmds import user_stats, user_name, remna_create_user, delete_devices, has_user_sub
from handlers.keyboards import choose_action
from payment.yookassa import create_payment
from config import payment_config, tg_config

logger = logging.getLogger(__name__)
router = Router()

one_month = payment_config.one_month
three_month = payment_config.three_month
one_year = payment_config.one_year
return_url = payment_config.return_url
tg_proxy = tg_config.proxy

# главное меню подписок по кнопке Подписки
@router.callback_query(F.data == 'subs')
async def subs_menu(callback: CallbackQuery):
    await callback.answer()
    tg_id = str(callback.from_user.id)
    res = await has_user_sub(tg_id=tg_id)

    # главная кнопка Подписки
    buttons = [
        [InlineKeyboardButton(text='Купить подписку', callback_data=f"{'is_buy' if res else 'month_'}",
                              style='success', icon_custom_emoji_id='5258165702707125574')],
        [InlineKeyboardButton(text='Мои подписки', callback_data='get_subs', 
                              style='success', icon_custom_emoji_id='5226513232549664618')],
        [InlineKeyboardButton(text='Пробный период', callback_data='AYS',
                              style='danger', icon_custom_emoji_id='5258105663359294787')]]

    if tg_proxy:
        buttons.append([InlineKeyboardButton(text='Прокси для тг', callback_data='proxy', 
                                             style='primary', icon_custom_emoji_id='5258073068852485953')])

    buttons.append([InlineKeyboardButton(text='В меню', callback_data='menu', icon_custom_emoji_id='5257963315258204021')])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_caption(caption='<b>— — Подписки — —</b>\n\n\n'
                                                '<i>Выберите действие кнопками ниже</i>',
                                                parse_mode='HTML',
                                                reply_markup=kb)


# кнопка Прокси (работает только если указан tg_proxy)
@router.callback_query(F.data == 'proxy')
async def proxy(callback: CallbackQuery):
    await callback.answer()
    back_subs = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Подключить', url=tg_proxy, icon_custom_emoji_id='5323404142809467476', style='success')],
        [InlineKeyboardButton(text='Назад', callback_data='subs', icon_custom_emoji_id='5258236805890710909')]
    ])
    await callback.message.edit_caption(caption='<b>— — Прокси — —</b>\n\n'
                                                f'Ссылка на наш прокси:\n\n{tg_proxy}\n\n'
                                                'Прокси полностью бесплатный, вы также можете делиться им с другими людьми!',
                                                parse_mode='HTML',
                                                reply_markup=back_subs)


def sub_action(users: dict[str, str], page=None) -> InlineKeyboardMarkup:
    """Возвращает клавиатуру для выбора подписок, с которой пользователь будет взаимодействовать"""
    builder = InlineKeyboardBuilder()
    for username, uuid in users.items():
        builder.button(
            text=username,
            callback_data=f"sub_action_{str(uuid)}",
            style='primary',
            icon_custom_emoji_id='5260399854500191689'
        )
    builder.button(text="Назад", callback_data="subs", icon_custom_emoji_id='5258236805890710909')
    return builder.adjust(1).as_markup()


# кнопка Мои подписки
@router.callback_query(F.data == 'get_subs')
async def get_subs(callback: CallbackQuery):
    tg_id = str(callback.from_user.id)
    subs_list = await user_stats(tg_id=tg_id)
    subs = await user_name(tg_id)

    if not subs_list:
        await callback.answer('У вас нет подписок!')
        return

    caption = ''
    for sub_n, sub in enumerate(subs_list):
        caption += f"\n<blockquote>{sub_n+1}. {sub}\n"

    # если подписок несколько
    if sub_n:
        text = "Выберите подписку для управления:"
        kb = sub_action(subs)

    else:
        text = "<i>Для продления подписки нажмите кнопку <b>Продлить</b></i>"
        uuid = str(list(subs.values())[0])
        kb = choose_action(uuid)
    
    await callback.answer()
    await callback.message.edit_caption(caption=f"<b>— — Подписки — —</b>\n\n{caption}\n{text}",
                                                parse_mode='HTML',
                                                reply_markup=kb)


# кнопка управления выбранной подпиской
@router.callback_query(F.data.startswith("sub_action_"))
async def sub_control(callback: CallbackQuery):
    uuid = callback.data.removeprefix('sub_action_')
    caption = await user_stats(uuid=uuid)

    await callback.answer()
    await callback.message.edit_caption(caption=f"<b>— — Управление подпиской — —</b>\n\n<blockquote>{caption}\n\n"
                                                'Выберите действие:',
                                                parse_mode='HTML',
                                                reply_markup=choose_action(uuid, one=False))

# кнопка управления устройствами
@router.callback_query(F.data.startswith("device_"))
async def device_control(callback: CallbackQuery):
    await callback.answer()
    uuid = callback.data.removeprefix('device_')

    # кнопка Сбросить устройства
    device_delete = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Сбросить устройства', callback_data=f'delete_device_{uuid}', 
                              style='danger', icon_custom_emoji_id='5260687681733533075')],
        [InlineKeyboardButton(text='Назад', callback_data='get_subs', icon_custom_emoji_id='5258236805890710909')]
    ])

    await callback.message.edit_caption(caption='<b>— — Управление устройствами — —</b>\n\n\n'
                                        'Если вы использовали подписку в нескольких приложениях, из-за чего подписка не добавляется в другом приложении'
                                        ' или на другом устройстве, нажмите кнопку "Сбросить устройства". Это удалит все привязанные устройства к подписке и позволит использовать её на новом устройстве и приложениях.'
                                        ' Подписка останется на всех подключённых устройствах и начнёт считаться устройством при первом её обновлении',
                                        parse_mode='HTML',
                                        reply_markup=device_delete)

# кнопка Сбросить устройства
@router.callback_query(F.data.startswith("delete_device_"))
async def delete_device(callback: CallbackQuery):
    uuid = callback.data.removeprefix('delete_device_')
    await delete_devices(uuid=uuid)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='В меню', callback_data='menu', icon_custom_emoji_id='5257963315258204021')]
    ])

    await callback.answer()
    await callback.message.edit_caption(caption=f'<b>— — Сброс устройств — —</b>\n\n\n'
                                                    'Устройства успешно сброшены! Можете использовать её на других устройствах!',
                                                    parse_mode='HTML',
                                                    reply_markup=kb)


# кнопка Купить подписку. выполняется если у клиента уже есть подписка
@router.callback_query(F.data == "is_buy")
async def is_buy(callback: CallbackQuery):

    # кнопка выбора новой подписки при наличии активной
    buy_mk = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Новая подписка', callback_data='month_', 
                              style='success', icon_custom_emoji_id='5258108352008823107')],
        [InlineKeyboardButton(text='Мои подписки', callback_data='get_subs',
                              style='primary', icon_custom_emoji_id='5226513232549664618')],
        [InlineKeyboardButton(text='Назад', callback_data='subs', icon_custom_emoji_id='5258236805890710909')]
    ])

    await callback.answer()
    await callback.message.edit_caption(caption='<b>— — Подписки — —</b>\n\n\n'
                                                'У вас есть активные подписки. Если вы хотите купить новую, нажмите кнопку "Новая подписка"',
                                                reply_markup=buy_mk,
                                                parse_mode='HTML')


def time_choose(user_uuid: str | None) -> InlineKeyboardMarkup:
    """Кливиатура с выбором времени покупки/продления подписки"""
    callback = 'agreement_'

    if user_uuid:
        callback = f'agreement_{user_uuid}_'

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f'1 месяц ({one_month}₽)', callback_data=f'{callback}1', icon_custom_emoji_id='5258165702707125574')],
        [InlineKeyboardButton(text=f'3 месяца ({three_month}₽)', callback_data=f'{callback}3', icon_custom_emoji_id='5258165702707125574')],
        [InlineKeyboardButton(text=f'12 месяцев ({one_year}₽)', callback_data=f'{callback}12', icon_custom_emoji_id='5258165702707125574')],
        [InlineKeyboardButton(text='Назад', callback_data='subs', icon_custom_emoji_id='5258236805890710909')]
    ])


# продление или покупка подписки
@router.callback_query(F.data.startswith("month_"))
async def renewal_month(callback: CallbackQuery):
    await callback.answer()
    uuid = callback.data.removeprefix('month_')
    caption = ["Подписка", "Выберите срок подписки:"]

    if uuid:
        caption = ["Продление подписки", "Выберите срок продления подписки:"]

    await callback.message.edit_caption(caption=f'<b>— — {caption[0]} — —</b>\n\n\n'
                                        f'{caption[1]}',
                                        reply_markup=time_choose(uuid),
                                        parse_mode='HTML')

# предварительное соглашение с пользователем перед оплатой
@router.callback_query(F.data.startswith('agreement_'))
async def buy_month(callback: CallbackQuery):
    full = callback.data.removeprefix('agreement_')
    suffix = {"1": "", "3": "а", "12": "ев"}

    if '_' in full:
        caption = ['продление подписки', 'После оплаты подписка продлится на выбранный срок.']
        uuid = full.split("_")[0]
        month = full.split("_")[1]
    else:
        caption = ['подписку', 'После оплаты вы получите ссылку на подписку и инструкцию к ней.']
        uuid = ''
        month = full

    # кнопка оплаты подписки
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Перейти к оплате', callback_data=f'upay_{full}', 
                              style='success', icon_custom_emoji_id='5258204546391351475')],
        [InlineKeyboardButton(text='Назад', callback_data=f'month_{uuid}', icon_custom_emoji_id='5258236805890710909')]
    ])

    await callback.answer()
    await callback.message.edit_caption(caption='<b>— — Оплата — —</b>\n\n\n'
                                                f'Вы выбрали {caption[0]} на {month} месяц{suffix[month]}!\n'
                                                f'{caption[1]}\n\n\n'
                                                'Для продолжения нажмите кнопку <b>Оплатить</b>',
                                                reply_markup=kb,
                                                parse_mode='HTML')


# создание платежа
@router.callback_query(F.data.startswith('upay_'))
async def upay(callback: CallbackQuery, bot_info):
    month = callback.data.removeprefix('upay_')
    user_id = callback.from_user.id
    username = callback.from_user.username if callback.from_user.username else str(user_id)
    uuid = ''

    if '_' in month:
        uuid = month.split("_")[0]
        month = month.split("_")[1]

    suffix = {"1": "", "3": "а", "12": "ев"}

    global return_url

    if not return_url:
        return_url = f"tg://resolve?domain={bot_info.username}"

    payment = await create_payment(
        user_id=user_id,
        username=username,
        month=month,
        return_url=return_url,
        uuid=uuid
    )
    text = f"Для оплаты {'продления ' if uuid else ''}подписки на {month} месяц{suffix[month]} нажмите кнопку 'Оплатить'"

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Оплатить", url=payment)]])
    await callback.answer()
    await callback.message.edit_caption(caption=f"<b>— — Оплата подписки — —</b>\n\n\n{text}", reply_markup=kb, parse_mode='HTML')


# кнопка Пробный период. Спрашивается, уверен ли пользователь
@router.callback_query(F.data == 'AYS') # are you sure (дофига англичанин, да)
async def ays(callback: CallbackQuery):
    tg_id = str(callback.from_user.id)
    user_has_sub = await has_user_sub(tg_id=tg_id)

    buttons = []
    text = 'У вас уже есть подписка, пробный период недоступен!'
    
    if not user_has_sub:
        text = 'Вы уверены, что хотите активировать пробный период? Он действует 3 дня и позволяет оценить качество наших услуг. '\
            'Пробный период доступен только для новых пользователей и может быть активирован только один раз.'
        buttons.append(
        [InlineKeyboardButton(text='Активировать', callback_data='test_period', 
                              style='danger', icon_custom_emoji_id='5323761960829862762')])

    buttons.append([InlineKeyboardButton(text='Назад', callback_data='subs', icon_custom_emoji_id='5258236805890710909')])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.answer()
    await callback.message.edit_caption(caption=f"<b>— — Пробный период — —</b>\n\n\n{text}",
                                                parse_mode='HTML',
                                                reply_markup=kb)


# выдача пробной подписки
@router.callback_query(F.data == 'test_period')
async def testPeriod(callback: CallbackQuery):
    tg_id = str(callback.from_user.id)
    username = callback.from_user.username if callback.from_user.username else tg_id
    sub = await remna_create_user(username, tg_id, 0.10)

    test_sub_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Инструкция', callback_data='manual', style='primary', icon_custom_emoji_id='5258328383183396223')],
        [InlineKeyboardButton(text='В меню', callback_data='menu', icon_custom_emoji_id='5257963315258204021')]
    ])
    
    await callback.answer()
    await callback.message.edit_caption(caption="<b>— — Пробный период — —</b>\n\n\n"
                                                "Пробный период на 3 дня активирован! Ваша подписка:\n\n"
                                                f"{sub}",
                                                parse_mode='HTML',
                                                reply_markup=test_sub_kb)
    logger.info(f"Пробная подписка на 3 дня успешно выдана пользователю {username}")