import logging
from aiogram import F, Router, Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from handlers.misc import choose_action, day_word, sub_action, suffix, price_list, errors_loging

from service.remna import remna
from payment.yookassa import create_payment

from database.db import database
from config import config


logger = logging.getLogger(__name__)
router = Router()
return_url = config.yookassa.return_url


# главное меню подписок по кнопке Подписки
@router.callback_query(F.data == 'subs')
@errors_loging
async def subs_menu(callback: CallbackQuery):
    await callback.answer(cache_time=1)
    tg_id = str(callback.from_user.id)
    res = await remna.has_user_sub(tg_id=tg_id)

    builder = InlineKeyboardBuilder()
    builder.button(
        text='Новая подписка', 
        callback_data=f"{'is_buy' if res else 'month_'}",
        style='success', 
        icon_custom_emoji_id='5258362837411045098'
    )
    if res:
        builder.button(
            text='Мои подписки', 
            callback_data='get_subs', 
            style='primary',
            icon_custom_emoji_id='5258513401784573443'
        )
    else:
        builder.button(
            text='Пробный период', 
            callback_data='AYS',
            style='primary', 
            icon_custom_emoji_id='5199457120428249992'
        )

    if config.telegram.proxy:
        builder.button(
            text='ТГ Прокси', 
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
        caption='<i>Выберите действие кнопками ниже</i>',
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )


# кнопка Прокси (работает только если указан tg_proxy)
@router.callback_query(F.data == 'proxy')
@errors_loging
async def proxy(callback: CallbackQuery):
    await callback.answer(cache_time=1)
    builder = InlineKeyboardBuilder()

    builder.button(
        text='Подключить',
        url=config.telegram.proxy, 
        icon_custom_emoji_id='5323404142809467476', 
        style='success'
    )
    builder.button(
        text='Назад', 
        callback_data='subs', 
        icon_custom_emoji_id='5258236805890710909'
    )
    await callback.message.edit_caption(
        caption=f'Наш прокси:\n\n{config.telegram.proxy}\n\n'
        '<blockquote><tg-emoji emoji-id="5357069174512303778">✅</tg-emoji> Он полностью бесплатный, вы также можете делиться им с другими людьми!</blockquote>',
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )


# кнопка Мои подписки
@router.callback_query(F.data == 'get_subs')
@errors_loging
async def get_subs(callback: CallbackQuery):
    tg_id = str(callback.from_user.id)
    subs_list = await remna.user_stats(tg_id=tg_id)
    if not subs_list:
        await callback.answer(
            text='У вас нет подписок!',
            cache_time=1
        )
        return

    caption = ''.join(sub for sub in subs_list)
    subs_uuids = await remna.user_name(tg_id)

    # если подписок несколько
    if len(subs_list) > 1:
        text = "<i>Выберите подписку для управления:</i>"
        kb = sub_action(users=subs_uuids, tg_id=tg_id)

    else:
        text = "<i>Выберите действие:</i>"
        uuid = str(list(subs_uuids.values())[0])
        kb = choose_action(uuid)
    
    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption=f"{caption}{text}",
        parse_mode='HTML',
        reply_markup=kb
    )


# кнопка управления выбранной подпиской
@router.callback_query(F.data.startswith("sub_action_"))
@errors_loging
async def sub_control(callback: CallbackQuery):
    uuid = callback.data.removeprefix('sub_action_')
    caption = await remna.user_stats(uuid=uuid)

    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption=f"{caption[0]}<i>Выберите действие:</i>",
        parse_mode='HTML',
        reply_markup=choose_action(uuid, one=False)
    )


# кнопка управления устройствами
@router.callback_query(F.data.startswith("device_"))
@errors_loging
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
        caption='Если подписка не добавляется на новом устройстве или в другом приложении, нажмите <b>«Сбросить устройства»</b>\n\n'
        '<tg-emoji emoji-id="5258474669769497337">❗️</tg-emoji> Это отвяжет все ранее подключённые устройства '
        'и позволит подключить подписку снова. Текущие подключения продолжат работать до их обновления.',
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )


# кнопка Сбросить устройства
@router.callback_query(F.data.startswith("delete_device_"))
@errors_loging
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
        caption='Устройства успешно сброшены\n\n'
        '<tg-emoji emoji-id="5260341314095947411">✅</tg-emoji> Можете использовать подписку на других устройствах!',
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )


# кнопка Купить подписку. выполняется если у клиента уже есть подписка
@router.callback_query(F.data == "is_buy")
@errors_loging
async def is_buy(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()

    builder.button(
        text='Мои подписки', 
        callback_data='get_subs',
        style='primary', 
        icon_custom_emoji_id='5226513232549664618'
    )
    builder.button(
        text='Купить новую', 
        callback_data='month_', 
        style='primary', 
        icon_custom_emoji_id='5258108352008823107'
    )
    builder.button(
        text='Назад', 
        callback_data='subs', 
        icon_custom_emoji_id='5258236805890710909'
    )
    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption='<b>У вас УЖЕ ЕСТЬ активные подписки!</b>\n\n'
        '<tg-emoji emoji-id="5258474669769497337">❗️</tg-emoji> Если вы хотите продлить существующую подписку, перейдите в раздел с вашими подписками',
        reply_markup=builder.adjust(1).as_markup(),
        parse_mode='HTML'
    )


def time_choose(user_uuid: str | int) -> InlineKeyboardMarkup:
    """Кливиатура с выбором времени покупки/продления подписки"""
    callback = 'agreement_'
    sub_count = 1

    if user_uuid:
        callback = f'agreement_{user_uuid}_'

    if user_uuid.isdigit():
        sub_count = user_uuid

    builder = InlineKeyboardBuilder()

    for month, price in price_list.items():
        if price:
            builder.button(
                text=f'{month} месяц{suffix[month]} ({int(price) * int(sub_count)}₽)',
                callback_data=f'{callback}{month}',
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
@errors_loging
async def renewal_month(callback: CallbackQuery):
    await callback.answer(cache_time=1)
    uuid = callback.data.removeprefix('month_')

    await callback.message.edit_caption(
        caption=f'<i>Выберите срок {"продления " if uuid else ""}подписки</i>',
        reply_markup=time_choose(uuid),
        parse_mode='HTML'
    )


# предварительное соглашение с пользователем перед оплатой
@router.callback_query(F.data.startswith('agreement_'))
@errors_loging
async def buy_month(callback: CallbackQuery):
    full = callback.data.removeprefix('agreement_')
    text = ''
    x = 1

    start_text = '<tg-emoji emoji-id="5258474669769497337">❗️</tg-emoji> Нажимая кнопку <b>«Перейти к оплате»</b> вы подтверждаете, что ознакомились и согласны с'
    terms_text = f'<a href="{config.telegram.terms_url}">Условиями пользования</a>'
    privacy_text = f'<a href="{config.telegram.privacy_url}">Политикой конфиденциальности</a>'
    

    if config.telegram.terms_url and config.telegram.privacy_url:
        x = 2
        text = f'{start_text} {terms_text} и {privacy_text}.\n\n'
    elif config.telegram.terms_url:
        text = f'{start_text} {terms_text}.\n\n'
    elif config.telegram.privacy_url:
        text = f'{start_text} {privacy_text}.\n\n'

    if '_' in full:
        uuid = full.split("_")[0]
        month = full.split("_")[1]
        caption = ['продление подписки', 'После оплаты подписка продлится на выбранный срок.']
        if uuid.isdigit():
            caption = ['продление подписок', 'После оплаты подписки продлятся на выбранный срок']

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
    if config.telegram.terms_url:
        builder.button(
            text='Условия пользования',
            url=config.telegram.terms_url,
            style='primary',
            icon_custom_emoji_id='5249231689695115145'
        )
    if config.telegram.privacy_url:
        builder.button(
            text='Политика конфеденциальности',
            url=config.telegram.privacy_url,
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
        caption=f'Вы выбрали {caption[0]} на {month} месяц{suffix[month]}!\n\n'
        f'<tg-emoji emoji-id="5260341314095947411">✅</tg-emoji> {caption[1]}\n\n{text}'
        '<i>Для продолжения нажмите кнопку <b>«Перейти к оплате»</b></i>',
        reply_markup=builder.adjust(1, x).as_markup(),
        parse_mode='HTML'
    )


# создание платежа
@router.callback_query(F.data.startswith('upay_'))
@errors_loging
async def upay(callback: CallbackQuery, bot_info):
    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption="<i>Ссылка для оплаты формируется, подождите секунду...\n</i>",
        parse_mode='HTML'
    )
    month = callback.data.removeprefix('upay_')
    user_id = callback.from_user.id
    
    username = callback.from_user.username if callback.from_user.username else str(user_id)
    uuid = ''

    if not await database.users.get_user(user_id):
        await callback.message.edit_caption(
            caption='Произошла ошибка! Для корректной работы перезапустите бота командой /start',
            parse_mode='HTML'
        )
        return

    if '_' in month:
        uuid, month = (i for i in month.split("_"))

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

    builder = InlineKeyboardBuilder()
    builder.button(
        text="Оплатить", 
        url=payment,
        icon_custom_emoji_id='5258204546391351475',
        style="success"
    )
    builder.button(
        text='В меню', 
        callback_data='menu', 
        icon_custom_emoji_id='5257963315258204021'
    )

    await callback.message.edit_caption(
        caption='<i>Нажмите на кнопку для перехода на страницу оплаты</i>', 
        reply_markup=builder.adjust(1).as_markup(), 
        parse_mode='HTML'
    )


# кнопка Пробный период. Спрашивается, уверен ли пользователь
@router.callback_query(F.data == 'AYS') # are you sure (дофига англичанин, да)
@errors_loging
async def ays(callback: CallbackQuery):
    tg_id = str(callback.from_user.id)
    user_has_sub = await remna.has_user_sub(tg_id=tg_id)

    builder = InlineKeyboardBuilder()
    text = '<tg-emoji emoji-id="5258474669769497337">❗️</tg-emoji> У вас уже есть подписка, пробный период недоступен!'
    
    if not user_has_sub:
        text = f'Пробный период действует {config.subscription.trial_days} {day_word(config.subscription.trial_days)} и позволяет оценить качество наших услуг.\n\n'\
                '<tg-emoji emoji-id="5258474669769497337">❗️</tg-emoji> Он доступен только для новых пользователей и может быть активирован только один раз'
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
        caption=text,
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )


# выдача пробной подписки
@router.callback_query(F.data == 'test_period')
@errors_loging
async def test_period(callback: CallbackQuery, bot: Bot):
    tg_id = str(callback.from_user.id)
    username = callback.from_user.username if callback.from_user.username else tg_id
    sub = await remna.create_user(
        username=username, 
        tg_id=tg_id, 
        days=config.subscription.trial_days, 
        traffic=config.subscription.trial_traffic,
        device_limit=config.subscription.trial_devices
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
        caption=f"Пробный период на {config.subscription.trial_days} {day_word(config.subscription.trial_days)} активирован!\n\n"
        f"<tg-emoji emoji-id='5260416304224936047'>✅</tg-emoji> Ваша подписка:\n\n{sub}",
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )
    a_link = f'<a href="tg://user?id={username}">' if username.isdigit() else f'<a href="tg://resolve?domain={username}">'
    emoji = '<tg-emoji emoji-id="5258258882022612173">⌛️</tg-emoji>'

    log_text = f'{emoji} Пользователь {a_link}<b>{username}</b></a> активировал пробный период на {config.subscription.trial_days} {day_word(config.subscription.trial_days)}!'
    
    if config.telegram.log_chat_id:
            await bot.send_message(
                chat_id=config.telegram.log_chat_id,
                message_thread_id=config.telegram.log_trial_topic_id,
                text=log_text,
                parse_mode='HTML'
            )
    logger.info(f"Пробная подписка на {config.subscription.trial_days} {day_word(config.subscription.trial_days)} успешно выдана пользователю {username}")