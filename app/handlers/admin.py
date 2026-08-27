from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from service.remna import remna
from handlers.misc import sub_action, get_random_photo, errors_loging, send_to_user
from database.db import database

from config import config

router = Router()


class AdminStates(StatesGroup):
    waiting_for_user = State()


def admin_back(has_caption: bool = False):
    builder = InlineKeyboardBuilder()
    
    if has_caption:
        builder.button(
            text='В меню',
            callback_data='admin_menu_no_caption',
            icon_custom_emoji_id='5258236805890710909'
        )
        return builder.adjust(1).as_markup()

    builder.button(
        text='В меню', 
        callback_data='admin_menu',
        icon_custom_emoji_id='5258236805890710909'
    )
    return builder.adjust(1).as_markup()

def admin_kb():
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Управление пользователями', 
        callback_data='admin_users', 
        icon_custom_emoji_id='5226513232549664618',
        style='success'
    )
    builder.button(
        text='Уведомление пользователям',
        callback_data='admin_notify',
        icon_custom_emoji_id='5258073068852485953',
        style='primary'
    )
    builder.button(
        text='Промокоды',
        callback_data='admin_promocodes',
        icon_custom_emoji_id='5258204546391351475',
        style='primary'
    )
    builder.button(
        text='В меню',
        callback_data='menu', 
        icon_custom_emoji_id='5257963315258204021'
    )
    return builder.adjust(1).as_markup()


@router.callback_query(F.data == 'admin_menu')
@errors_loging
async def admin_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption='<b>— — Админ панель — —</b>\n\n\n<i>Выберите действие кнопками ниже</i>',
        reply_markup=admin_kb(),
        parse_mode='HTML'
    )


@router.callback_query(F.data == 'admin_menu_no_caption')
@errors_loging
async def admin_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await callback.answer(cache_time=1)
    await callback.message.delete()

    await callback.message.answer_photo(
        photo=FSInputFile(get_random_photo()),
        caption='<b>— — Админ панель — —</b>\n\n\n<i>Выберите действие кнопками ниже</i>',
        reply_markup=admin_kb(),
        parse_mode='HTML'
    )


@router.callback_query(F.data == 'admin_users')
@errors_loging
async def admin_user(callback: CallbackQuery, state: FSMContext):
    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption='<b>— — Админ панель — —</b>\n\n\n'
        'Введите юзернейм или id пользователя для поиска его подписок',
        reply_markup=admin_back(),
        parse_mode='HTML'
    )
    await state.set_state(AdminStates.waiting_for_user)


def admin_action(username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Дата истечения',
        callback_data=f'admin_data_{username}',
        style='success', 
        icon_custom_emoji_id='5258105663359294787'
    )
    builder.button(
        text='Устройства',
        callback_data=f'admin_devices_{username}',
        style='primary', 
        icon_custom_emoji_id='5258508428212445001'
    )
    builder.button(
        text='Трафик',
        callback_data=f'admin_traffic_{username}',
        style='primary', 
        icon_custom_emoji_id='5258336354642697821'
    )
    builder.button(
        text='Остановить',
        callback_data=f'admin_stop_{username}',
        style='danger', 
        icon_custom_emoji_id='5260249440450520061'
    )
    builder.button(
        text='Удалить',
        callback_data=f'admin_delete_{username}',
        style='danger', 
        icon_custom_emoji_id='5258389041006518073'
    )
    builder.button(
        text='Назад',
        callback_data='admin_users', 
        icon_custom_emoji_id='5258236805890710909'
    )
    return builder.adjust(1, 2, 2).as_markup()


@router.message(AdminStates.waiting_for_user)
@errors_loging
async def admin_sub(message: Message, state: FSMContext):
    value: str = message.text.strip()
    if not value.isdigit():
        value = await database.users.get_telegram_id(value.replace('@', '').lower())

    subs_list = await remna.user_stats(tg_id=value)

    if not subs_list:
        await message.answer(
            text='У пользователя нет активных подписок.',
            reply_markup=admin_back(True)
        )
        return

    caption = ''
    if len(subs_list) < 5:
        caption = caption.join(sub for sub in subs_list)
    
    usernames = await remna.user_name(value)

    # если подписок несколько
    if len(subs_list) > 1:
        text = "<i>Выберите подписку для управления:</i>"
        kb = sub_action(users=usernames, tg_id=value, admin=True)

    else:
        text = "<i>Выберите действие:</i>"
        kb = admin_action(usernames[0])

    await message.answer_photo(
        caption=f"{caption}{text}",
        photo=FSInputFile(get_random_photo()),
        parse_mode='HTML',
        reply_markup=kb
    )

    await state.clear()


# кнопка управления выбранной подпиской
@router.callback_query(F.data.startswith("admin_sub_action_"))
@errors_loging
async def admin_subs(callback: CallbackQuery):
    uuid = callback.data.removeprefix('admin_sub_action_')
    caption = await remna.user_stats(uuid=uuid)

    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption=f"{caption[0]}<i>Выберите действие:</i>",
        parse_mode='HTML',
        reply_markup=admin_action(uuid)
    )


@router.callback_query(F.data.startswith("admin_delete_"))
@errors_loging
async def admin_delete(callback: CallbackQuery):
    uuid: str = callback.data.removeprefix("admin_delete_")
    caption = '<b>— — Удаление подписки — —</b>\n\n\n'\
        '<tg-emoji emoji-id="5258474669769497337">❗️</tg-emoji> вы <b>УВЕРЕНЫ</b> что хотите удалить эту подписку? '\
        'Это действие <b>НЕОБРАТИМО</b>, подписка удалится <b>НАВСЕГДА, БЕЗ ВОЗМОЖНОСТИ ВОССТАНОВЛЕНИЯ!</b>\n\n\n'\
        '<i>Если вы ТОЧНО уверены в своём решении, то нажмите соответствующую кнопку</i>'

    builder = InlineKeyboardBuilder()

    builder.button(
        text='Удалить',
        callback_data=f'admin_purge_delete_{uuid}',
        style='danger', 
        icon_custom_emoji_id='5258389041006518073'
    )
    builder.button(
        text='Назад',
        callback_data=f'admin_sub_action_{uuid}',
        style='success',
        icon_custom_emoji_id='5258236805890710909'
    )
    
    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption=caption,
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )


def notification_kb() -> InlineKeyboardMarkup:
    """Клавиатура для уведомлений пользователя"""
    builder = InlineKeyboardBuilder()

    if config.telegram.support_link:
        builder.button(
            text='Поддержка',
            url=config.telegram.support_link,
            icon_custom_emoji_id='5316727448644103237',
            style='primary'
        )
    
    builder.button(
        text='В меню', 
        callback_data='menu',
        icon_custom_emoji_id='5257963315258204021'
    )

    return builder.adjust(1).as_markup()


@router.callback_query(F.data.startswith("admin_purge_delete_"))
@errors_loging
async def admin_purge_delete(callback: CallbackQuery, bot: Bot):
    uuid: str = callback.data.removeprefix("admin_purge_delete_")
    admin_username = callback.from_user.username if callback.from_user.username else callback.from_user.id

    telegram_id, username = await remna.delete_user(uuid)
    caption = '<b>— — Удаление подписки — —</b>\n\n\n'\
        f'<tg-emoji emoji-id="5260416304224936047">✅</tg-emoji> Подписка {username} была успешно удалена!'

    builder = InlineKeyboardBuilder()
    builder.button(
        text='В меню', 
        callback_data='admin_menu',
        icon_custom_emoji_id='5258236805890710909'
    )

    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption=caption,
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )

    text = '<b>— — Уведомление — —</b>\n\n\n'\
        f'<tg-emoji emoji-id="5258474669769497337">❗️</tg-emoji> Ваша подписка {username} была удалена! По возникшим вопросам обращайтесь в тех поддержку!'

    await send_to_user(bot=bot, user=telegram_id, text=text, kb=notification_kb())
    logger.info(f"Подписка {username} была успешно удалена админом {admin_username}!")


@router.callback_query(F.data.startswith("admin_stop_"))
@errors_loging
async def admin_stop(callback: CallbackQuery):
    uuid: str = callback.data.removeprefix("admin_stop_")
    caption = '<b>— — Отключение подписки — —</b>\n\n\n'\
        '<tg-emoji emoji-id="5258474669769497337">❗️</tg-emoji> Безопасная остановка подписки у пользователя. '\
        'После отключения подписки пользователь не сможет пользоваться подпиской до того, как вы её не включите снова\n\n\n'\
        '<i>Если вы желаете отключить подписку, нажмите соответствующую кнопку</i>'

    builder = InlineKeyboardBuilder()

    builder.button(
        text='Отключить',
        callback_data=f'admin_disable_{uuid}',
        style='danger', 
        icon_custom_emoji_id='5258389041006518073'
    )
    builder.button(
        text='Назад',
        callback_data=f'admin_sub_action_{uuid}',
        style='success',
        icon_custom_emoji_id='5258236805890710909'
    )
    
    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption=caption,
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )


@router.callback_query(F.data.startswith("admin_disable_"))
@errors_loging
async def admin_disable(callback: CallbackQuery, bot: Bot):
    uuid: str = callback.data.removeprefix("admin_disable_")
    admin_username = callback.from_user.username if callback.from_user.username else callback.from_user.id

    telegram_id, username = await remna.disable_user(uuid)
    caption = '<b>— — Отключение подписки — —</b>\n\n\n'\
        f'<tg-emoji emoji-id="5260416304224936047">✅</tg-emoji> Подписка {username} была успешно приостановлена!'

    builder = InlineKeyboardBuilder()
    builder.button(
        text='В меню', 
        callback_data='admin_menu',
        icon_custom_emoji_id='5258236805890710909'
    )

    await callback.answer(cache_time=1)
    await callback.message.edit_caption(
        caption=caption,
        parse_mode='HTML',
        reply_markup=builder.adjust(1).as_markup()
    )

    text = '<b>— — Уведомление — —</b>\n\n\n'\
        f'<tg-emoji emoji-id="5258474669769497337">❗️</tg-emoji> Ваша подписка {username} была приостановлена! По возникшим вопросам обращайтесь в тех поддержку!'
    
    await send_to_user(bot=bot, user=telegram_id, text=text, kb=notification_kb())
    logger.info(f"Подписка {username} была успешно приостановлена админом {admin_username}!")


@router.callback_query(F.data.startswith("admin_data_"))
@errors_loging
async def admin_data(callback: CallbackQuery, bot: Bot):
    uuid: str = callback.data.removeprefix("admin_data_")
    admin_username = callback.from_user.username if callback.from_user.username else callback.from_user.id
    ...


@router.callback_query(F.data.startswith("admin_devices_"))
@errors_loging
async def admin_devices(callback: CallbackQuery, bot: Bot):
    uuid: str = callback.data.removeprefix("admin_devices_")
    admin_username = callback.from_user.username if callback.from_user.username else callback.from_user.id
    ...


@router.callback_query(F.data.startswith("admin_traffic_"))
@errors_loging
async def admin_traffic(callback: CallbackQuery, bot: Bot):
    uuid: str = callback.data.removeprefix("admin_traffic_")
    admin_username = callback.from_user.username if callback.from_user.username else callback.from_user.id
    ...