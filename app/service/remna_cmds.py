import logging
from datetime import datetime, timedelta, timezone
from remnawave import RemnawaveSDK
from remnawave.models import CreateUserRequestDto, UpdateUserRequestDto, DeleteUserAllHwidDeviceRequestDto
from remnawave.exceptions.general import NotFoundError

from config import remna_config


logger = logging.getLogger(__name__)

token = remna_config.token
panel_url = remna_config.panel_url
domain = remna_config.sub_domain
hwid_limit = None

sdk = RemnawaveSDK(
    base_url=panel_url,
    token=token
)


# возвращает список telegram id пользователей, подписка которых истекает через день
# вызывается функция из файла start.py раз в час
async def expire_day(days=1) -> list[str]:
    start = 0
    users = []
    delta = datetime.now(timezone.utc) + timedelta(days=days)
    
    while True:
        response = await sdk.users.get_all_users(size=25, start=start)
        if not response.users:
            break
        
        for user in response.users:
            if delta >= user.expire_at and not user.description:
                users.append(user.telegram_id)
                await sdk.users.update_user(
                    UpdateUserRequestDto(uuid=user.uuid, description="Уведомлён"))
        start += 25
    
    return users


async def text_user_stats(user, hwid) -> str:
    """Формирует и возвращает текст с информацией о подписке по его uuid и hwid"""

    global hwid_limit

    # проверка глобального hwid лимита
    if hwid_limit is None:
        global_limit = await sdk.subscriptions_settings.get_settings()
        if global_limit.hwid_settings.enabled:
            hwid_limit = global_limit.hwid_settings.fallback_device_limit
        else:
            hwid_limit = False

    # лимит самого пользователя
    hwid_device = user.hwid_device_limit
    
    if hwid_device == 0:
        hwid_device = '<tg-emoji emoji-id="5271934788037517525">♾️</tg-emoji>'
    elif hwid_device is None:
        hwid_device = hwid_limit

    gb = lambda num: round(num / (1024 * 1024 * 1024), 2)

    active = '<tg-emoji emoji-id="5260342697075416641">❌</tg-emoji>'
    if user.status.lower() == 'active':
        active = '<tg-emoji emoji-id="5260416304224936047">✅</tg-emoji>'

    expire_time = user.expire_at.strftime('%d.%m.%Y')
    if int(user.expire_at.strftime('%Y')) >= 2099:
        expire_time = '<tg-emoji emoji-id="5271934788037517525">♾️</tg-emoji>'

    return (f"{user.username} {active}</blockquote>\n"
            f'<tg-emoji emoji-id="5258508428212445001">📱</tg-emoji> Количество устройств: <b>{len(hwid.devices)}</b>/{hwid_device}\n\n'
            f'<tg-emoji emoji-id="5199457120428249992">📆</tg-emoji> Дата истечения подписки: {expire_time}\n\n'
            f'<tg-emoji emoji-id="5258330865674494479">⚡️</tg-emoji> Трафик <i>(месяц/всё время)</i>: <b>{gb(user.used_traffic_bytes)}ГБ / {gb(user.lifetime_used_traffic_bytes)}ГБ</b>\n\n'
            f'<tg-emoji emoji-id="5260730055880876557">🔗</tg-emoji> Ссылка на подписку: <code>{domain}{user.short_uuid}</code> (<i>кликабельно</i>)\n'
            )


async def user_stats(tg_id: str | None = None, uuid: str | None =None) -> str | list[str] | None:
    """
    Функция получения статистики по tg_id или uuid.
    Возвращает список из инфы о всех подписках по тг айди или инфу о подписке по uuid.
    """
    if uuid:
        user = await sdk.users.get_user_by_uuid(uuid=uuid)
        hwid = await sdk.hwid.get_hwid_user(uuid=uuid)
        return await text_user_stats(user, hwid)
    if tg_id:
        subs = []
        users = await sdk.users.get_users_by_telegram_id(tg_id)
        for user in users:
            hwid = await sdk.hwid.get_hwid_user(uuid=str(user.uuid))
            subs.append(await text_user_stats(user, hwid))
        return subs
    return None


async def has_user_sub(tg_id: str) -> bool:
    """Возвращает истину при наличии у пользователя подписки"""
    if await sdk.users.get_users_by_telegram_id(tg_id):
        return True
    return False
    


async def user_name(tg_id: str) -> dict[str, str]:
    """Возвращает словарь с парами значений всех подписок username : uuid по tg_id"""
    users = await sdk.users.get_users_by_telegram_id(tg_id)
    res = {}

    for user in users:
        res[user.username] = user.uuid

    return res


async def delete_devices(uuid: str) -> None:
    """Сбрасывает все устройства для подписки"""
    request = DeleteUserAllHwidDeviceRequestDto(user_uuid=uuid)
    await sdk.hwid.delete_all_hwid_user(body=request)


async def remna_create_user(username: str, tg_id: str, month: int) -> str:
    """Создаёт подписку и возвращает её url"""
    end_date = datetime.now(timezone.utc) + timedelta(days=30*month)
    squad_uuid = 'ba78e6e0-a2db-49d4-9c0d-2320d9a8aad4'
    res_user = username
    i = 1

    # проверяем существует ли уже пользователь с таким именем, если да - добавляем цифру в конце, пока не найдём свободное имя
    while True:
        try:
            await sdk.users.get_user_by_username(username=res_user)
            res_user = f"{username}{i}"
            i += 1
        except NotFoundError:
            break

    description = ''
    if month < 1:
        description = "Пробная подписка"

    new_user = await sdk.users.create_user(
        CreateUserRequestDto(
            username=res_user,
            telegram_id=str(tg_id),
            expire_at=end_date,
            description=description,
            active_internal_squads=[str(squad_uuid)],
            traffic_limit_strategy="MONTH"
        )
    )

    return f'<code>{domain}{new_user.short_uuid}</code>'

async def update_user(uuid: str, month: int) -> str:
    """Обновляет подписку по её {uuid} на {month} месяцев и возвращает её название"""
    user = await sdk.users.get_user_by_uuid(uuid=uuid)

    # проверяем, истекла ли подписка
    if user.expire_at < datetime.now(timezone.utc):
        new_expire = datetime.now(timezone.utc) + timedelta(days=30*month)
    else:
        new_expire = user.expire_at + timedelta(days=30*month)

    await sdk.users.update_user(
        UpdateUserRequestDto(
            uuid=uuid,
            expire_at=new_expire,
            description='',
            traffic_limit_strategy="MONTH"
        )
    )
    return user.username