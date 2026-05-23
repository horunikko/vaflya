import logging
from aiogram import F, Router
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from service.remna_cmds import remna
from handlers.keyboards import choose_action, day_word
from payment.yookassa import create_payment
from config import payment_config, tg_config, sub_config


logger = logging.getLogger(__name__)
router = Router()


one_month = payment_config.one_month
three_month = payment_config.three_month
one_year = payment_config.one_year
return_url = payment_config.return_url

tg_proxy = tg_config.proxy


def gen_url(value: str | None) -> str | None:
    """Возвращает значение юзернейма/ссылки в качестве изначальной ссылки, либо ссылки на тг"""
    if not value or value.startswith('https://'):
        return value
    return f"https://{value}"


privacy_url = gen_url(tg_config.privacy_url)
terms_url = gen_url(tg_config.terms_url)

trial_days = sub_config.trial_days
trial_traffic = sub_config.trial_traffic
trial_devices = sub_config.trial_devices


# главное меню подписок по кнопке Подписки
@router.callback_query(F.data == 'subs')
async def subs_menu(callback: CallbackQuery):
    await callback.answer(cache_time=1)
    tg_id = str(callback.from_user.id)
    res = await remna.has_user_sub(tg_id=tg_id)

    builder = InlineKeyboardBuilder()
    builder.button(
        text='Новая подписка', 
        callback_data=f"{'is_buy' if res else 'month_'}",
        style='success', 
        icon_custom_emoji_id='5258165702707125574'
    )
    builder.button(
        text='Мои подписки', 
        callback_data='get_subs', 
        style='success', 
        icon_custom_emoji_id='5226513232549664618'
    )
    builder.button(
        text='Пробный период', 
        callback_data='AYS',
        style='danger', 
        icon_custom_emoji_id='5258105663359294787'
    )

    if tg_proxy:
        builder.button(
            text='Прокси для тг', 
            callback_data='proxy', 
            style='primary', 
            icon_custom_emoji_id='5258073068852485953'
        )

    builder.button(
        text='В меню', 
        callback_data='menu', 
        icon_custom_emoji_id='5257963315258204021'
    )
    await callback.message.edit_caption(
        caption='<b>— — Подписки — —</b>\n\n\n<i>Выберите действие кнопками ниже</i>',
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )


# кнопка Прокси (работает только если указан tg_proxy)
@router.callback_query(F.data == 'proxy')
async def proxy(callback: CallbackQuery):
    await callback.answer(cache_time=1)
    builder = InlineKeyboardBuilder()

    builder.button(
        text='Подключить', 
        url=tg_proxy, 
        icon_custom_emoji_id='5323404142809467476', 
        style='success'
    )
    builder.button(
        text='Назад', 
        callback_data='subs', 
        icon_custom_emoji_id='5258236805890710909'
    )
    await callback.message.edit_caption(
        caption=f'<b>— — Прокси — —</b>\n\nСсылка на наш прокси:\n\n{tg_proxy}\n\n'
        'Прокси полностью бесплатный, вы также можете делиться им с другими людьми!',
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )


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
    builder.button(
        text="Назад", 
        callback_data="subs", 
        icon_custom_emoji_id='5258236805890710909'
    )
    return builder.adjust(1).as_markup()


# кнопка Мои подписки
@router.callback_query(F.data == 'get_subs')
async def get_subs(callback: CallbackQuery):
    tg_id = str(callback.from_user.id)
    subs_list = await remna.user_stats(tg_id=tg_id)
    subs = await remna.user_name(tg_id)

    if not subs_list:
        await callback.answer(text='У вас нет подписок!', cache_time=1)
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
    
    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption=f"<b>— — Подписки — —</b>\n\n{caption}\n{text}",
        parse_mode='HTML',
        reply_markup=kb
    )


# кнопка управления выбранной подпиской
@router.callback_query(F.data.startswith("sub_action_"))
async def sub_control(callback: CallbackQuery):
    uuid = callback.data.removeprefix('sub_action_')
    caption = await remna.user_stats(uuid=uuid)

    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption="<b>— — Управление подпиской — —</b>"
        f"\n\n<blockquote>{caption}\n\nВыберите действие:",
        parse_mode='HTML',
        reply_markup=choose_action(uuid, one=False)
    )


# кнопка управления устройствами
@router.callback_query(F.data.startswith("device_"))
async def device_control(callback: CallbackQuery):
    await callback.answer(cache_time=1)
    uuid = callback.data.removeprefix('device_')

    builder = InlineKeyboardBuilder()
    builder.button(
        text='Сбросить устройства', 
        callback_data=f'delete_device_{uuid}', 
        style='danger', 
        icon_custom_emoji_id='5260687681733533075'
    )
    builder.button(
        text='Назад', 
        callback_data='get_subs', 
        icon_custom_emoji_id='5258236805890710909'
    )

    await callback.message.edit_caption(
        caption='<b>— — Управление устройствами — —</b>\n\n\n'
        'Если вы использовали подписку в нескольких приложениях, из-за чего подписка не добавляется в другом приложении'
        ' или на другом устройстве, нажмите кнопку "Сбросить устройства".'
        ' Это удалит все привязанные устройства к подписке и позволит использовать её на новом устройстве и приложениях.'
        ' Подписка останется на всех подключённых устройствах и начнёт считаться устройством при первом её обновлении',
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )


# кнопка Сбросить устройства
@router.callback_query(F.data.startswith("delete_device_"))
async def delete_device(callback: CallbackQuery):
    uuid = callback.data.removeprefix('delete_device_')
    await remna.delete_devices(uuid=uuid)

    builder = InlineKeyboardBuilder()

    builder.button(
        text='В меню', 
        callback_data='menu', 
        icon_custom_emoji_id='5257963315258204021'
    )

    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption=f'<b>— — Сброс устройств — —</b>\n\n\n'
        'Устройства успешно сброшены! Можете использовать её на других устройствах!',
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )


# кнопка Купить подписку. выполняется если у клиента уже есть подписка
@router.callback_query(F.data == "is_buy")
async def is_buy(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()

    builder.button(
        text='Купить новую', 
        callback_data='month_', 
        style='success', 
        icon_custom_emoji_id='5258108352008823107'
    )
    builder.button(
        text='Мои подписки', 
        callback_data='get_subs',
        style='primary', 
        icon_custom_emoji_id='5226513232549664618'
    )
    builder.button(
        text='Назад', 
        callback_data='subs', 
        icon_custom_emoji_id='5258236805890710909'
    )
    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption='<b>— — Подписки — —</b>\n\n\n'
        'У вас уже есть активные подписки. Если вы хотите продлить существующую подписку, перейдите в раздел с вашими подписками по кнопке "Мои подписки"',
        reply_markup=builder.adjust(1).as_markup(),
        parse_mode='HTML'
    )


def time_choose(user_uuid: str | None) -> InlineKeyboardMarkup:
    """Кливиатура с выбором времени покупки/продления подписки"""
    callback = 'agreement_'

    if user_uuid:
        callback = f'agreement_{user_uuid}_'

    builder = InlineKeyboardBuilder()

    builder.button(
        text=f'1 месяц ({one_month}₽)', 
        callback_data=f'{callback}1', 
        icon_custom_emoji_id='5258165702707125574',
        style='success'
    )
    builder.button(
        text=f'3 месяца ({three_month}₽)', 
        callback_data=f'{callback}3', 
        icon_custom_emoji_id='5258165702707125574',
        style='success'
    )
    builder.button(
        text=f'12 месяцев ({one_year}₽)', 
        callback_data=f'{callback}12', 
        icon_custom_emoji_id='5258165702707125574',
        style='success'
    )
    builder.button(
        text='Назад', 
        callback_data='subs', 
        icon_custom_emoji_id='5258236805890710909'
    )

    return builder.adjust(1).as_markup()


# продление или покупка подписки
@router.callback_query(F.data.startswith("month_"))
async def renewal_month(callback: CallbackQuery):
    await callback.answer(cache_time=1)
    uuid = callback.data.removeprefix('month_')
    caption = ["Подписка", "Выберите срок подписки:"]

    if uuid:
        caption = ["Продление подписки", "Выберите срок продления подписки:"]

    await callback.message.edit_caption(
        caption=f'<b>— — {caption[0]} — —</b>\n\n\n{caption[1]}',
        reply_markup=time_choose(uuid),
        parse_mode='HTML'
    )


# предварительное соглашение с пользователем перед оплатой
@router.callback_query(F.data.startswith('agreement_'))
async def buy_month(callback: CallbackQuery):
    full = callback.data.removeprefix('agreement_')
    suffix = {"1": "", "3": "а", "12": "ев"}

    text = ''
    start_text = '<tg-emoji emoji-id="5258474669769497337">❗️</tg-emoji> Перед оплатой вам необходимо принять'
    end_text = '. Нажимая кнопку <b>Перейти к оплате</b> вы подтверждаете, что ознакомились и согласны с применимыми условиями и политиками сервиса.\n\n\n'
    terms_text = f'<a href="{terms_url}">Условия пользования</a>'
    privacy_text = f'<a href="{privacy_url}">Политику конфиденциальности</a>'

    if terms_url and privacy_url:
        text = f'{start_text} {terms_text} и {privacy_text}{end_text}'
    elif terms_url:
        text = f'{start_text} {terms_text}{end_text}'
    elif privacy_url:
        text = f'{start_text} {privacy_text}{end_text}'

    if '_' in full:
        caption = ['продление подписки', 'После оплаты подписка продлится на выбранный срок.']
        uuid = full.split("_")[0]
        month = full.split("_")[1]
    else:
        caption = ['подписку', 'После оплаты вы получите ссылку на подписку и инструкцию к ней.']
        uuid = ''
        month = full

    builder = InlineKeyboardBuilder()

    builder.button(
        text='Перейти к оплате', 
        callback_data=f'upay_{full}', 
        style='success', 
        icon_custom_emoji_id='5258204546391351475'
    )
    if terms_url:
        builder.button(
            text='Условия пользования',
            url=terms_url,
            style='primary',
            icon_custom_emoji_id='5249231689695115145'
        )
    if privacy_url:
        builder.button(
            text='Политика конфеденциальности',
            url=privacy_url,
            style='primary',
            icon_custom_emoji_id='5258011929993026890'
        )
    builder.button(
        text='Назад', 
        callback_data=f'month_{uuid}', 
        icon_custom_emoji_id='5258236805890710909'
    )

    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption='<b>— — Оплата — —</b>\n\n\n'
        f'<tg-emoji emoji-id="5260341314095947411">✅</tg-emoji> Вы выбрали {caption[0]} на {month} месяц{suffix[month]}!\n'
        f'{caption[1]}\n\n\n'
        f'{text}'
        '<tg-emoji emoji-id="5260450573768990626">➡️</tg-emoji> Для продолжения нажмите кнопку <b>Перейти к оплате</b>',
        reply_markup=builder.adjust(1).as_markup(),
        parse_mode='HTML'
    )


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
    text = '<tg-emoji emoji-id="5258336354642697821">📃</tg-emoji> Нажмите <b>кнопку ниже</b> для перехода на страницу оплаты'

    builder = InlineKeyboardBuilder()
    builder.button(
        text="Оплатить", 
        url=payment,
        icon_custom_emoji_id='5258204546391351475',
        style="success"
    )

    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption=f"<b>— — Оплата подписки — —</b>\n\n\n{text}", 
        reply_markup=builder.adjust(1).as_markup(), 
        parse_mode='HTML'
    )


# кнопка Пробный период. Спрашивается, уверен ли пользователь
@router.callback_query(F.data == 'AYS') # are you sure (дофига англичанин, да)
async def ays(callback: CallbackQuery):
    tg_id = str(callback.from_user.id)
    user_has_sub = await remna.has_user_sub(tg_id=tg_id)

    builder = InlineKeyboardBuilder()
    text = 'У вас уже есть подписка, пробный период недоступен!'
    
    if not user_has_sub:
        text = f'Вы уверены, что хотите активировать пробный период? Он действует {trial_days} {day_word(trial_days)} и позволяет оценить качество наших услуг. '\
                'Пробный период доступен только для новых пользователей и может быть активирован только один раз.'
        builder.button(
            text='Активировать', 
            callback_data='test_period', 
            style='danger', 
            icon_custom_emoji_id='5323761960829862762'
        )

    builder.button(
        text='Назад', 
        callback_data='subs', 
        icon_custom_emoji_id='5258236805890710909'
    )

    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption=f"<b>— — Пробный период — —</b>\n\n\n{text}",
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )


# выдача пробной подписки
@router.callback_query(F.data == 'test_period')
async def test_period(callback: CallbackQuery):
    tg_id = str(callback.from_user.id)
    username = callback.from_user.username if callback.from_user.username else tg_id
    sub = await remna.create_user(
        username=username, 
        tg_id=tg_id, 
        days=trial_days, 
        traffic=trial_traffic,
        device_limit=trial_devices
    )

    builder = InlineKeyboardBuilder()
    builder.button(
        text='Инструкция', 
        callback_data='manual', 
        style='primary', 
        icon_custom_emoji_id='5258328383183396223'
    )
    builder.button(
        text='В меню', 
        callback_data='menu', 
        icon_custom_emoji_id='5257963315258204021'
    )
    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption="<b>— — Пробный период — —</b>\n\n\n"
        f"Пробный период на {trial_days} {day_word(trial_days)} активирован! Ваша подписка:\n\n{sub}",
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )
    logger.info(f"Пробная подписка на {trial_days} {day_word(trial_days)} успешно выдана пользователю {username}")