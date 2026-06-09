import logging
from datetime import datetime, timedelta, timezone
from remnawave import RemnawaveSDK
from remnawave.models import CreateUserRequestDto, UpdateUserRequestDto, DeleteUserAllHwidDeviceRequestDto
from remnawave.exceptions.general import NotFoundError

from config import config
from database.db import database


logger = logging.getLogger(__name__)


class Remnawave:
    def __init__(self, token, panel_url, hwid_limit):
        self.token = token
        self.panel_url = panel_url
        self.hwid_limit = hwid_limit

        self.sdk = RemnawaveSDK(base_url=self.panel_url, token=self.token)


    async def expire_day(self, days: int) -> list[str]:
        """Возвращает список из telegram id пользователей, чья подписка истекает через {days} дней"""
        start = 0
        users = []
        date = datetime.now(timezone.utc)
        delta = date + timedelta(days=days)
        
        while True:
            response = await self.sdk.users.get_all_users(size=25, start=start)
            if not response.users:
                break
            
            for user in response.users:
                if user.expire_at > date:

                    sub_days = await database.notifications.get_days(str(user.uuid))

                    # создание записи в бд при её отсутствии
                    if sub_days is None:
                        await database.notifications.create_or_update(str(user.uuid))
                        sub_days = 0
                        
                    # а вот тут уже идёт основная проверка
                    if delta >= user.expire_at and (days < sub_days or sub_days == 0):
                        if user.telegram_id:
                            users.append(user.telegram_id)
                        await database.notifications.create_or_update(uuid=str(user.uuid), notify_days=days)
            start += 25
        
        return users


    async def text_user_stats(self, user, hwid) -> str:
        """Формирует и возвращает текст с информацией о подписке по его uuid и hwid"""
        # проверка глобального hwid лимита
        if self.hwid_limit is None:
            global_limit = await self.sdk.subscriptions_settings.get_settings()

            if global_limit.hwid_settings.enabled:
                self.hwid_limit = global_limit.hwid_settings.fallback_device_limit
            else:
                self.hwid_limit = False

        # лимит самого пользователя
        hwid_device = user.hwid_device_limit
        
        if hwid_device == 0:
            hwid_device = '<tg-emoji emoji-id="5271934788037517525">♾️</tg-emoji>'
        elif hwid_device is None:
            hwid_device = self.hwid_limit

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
                f'<tg-emoji emoji-id="5260730055880876557">🔗</tg-emoji> Ссылка на подписку: <code>{user.subscription_url}</code> (<i>кликабельно</i>)\n'
                )


    async def user_stats(self, tg_id: str | int | None = None, uuid: str | None =None) -> str | list[str] | None:
        """Функция получения статистики по tg_id или uuid.
        Возвращает список из инфы о всех подписках по тг айди или инфу о подписке по uuid"""
        if uuid:
            user = await self.sdk.users.get_user_by_uuid(uuid=uuid)
            hwid = await self.sdk.hwid.get_hwid_user(uuid=uuid)
            return await self.text_user_stats(user, hwid)
        if tg_id:
            subs = []
            users = await self.sdk.users.get_users_by_telegram_id(str(tg_id))
            for user in users:
                hwid = await self.sdk.hwid.get_hwid_user(uuid=str(user.uuid))
                subs.append(await self.text_user_stats(user, hwid))
            return subs
        return None


    async def has_user_sub(self, tg_id: str | int) -> bool:
        """Возвращает истину при наличии у пользователя подписки"""
        return bool(await self.sdk.users.get_users_by_telegram_id(str(tg_id)))
        

    async def user_name(self, tg_id: str | int) -> dict[str, str]:
        """Возвращает словарь с парами значений всех подписок username : uuid по tg_id"""
        users = await self.sdk.users.get_users_by_telegram_id(str(tg_id))
        res = {}

        for user in users:
            res[user.username] = user.uuid

        return res


    async def delete_devices(self, uuid: str) -> None:
        """Сбрасывает все устройства для подписки"""
        request = DeleteUserAllHwidDeviceRequestDto(user_uuid=uuid)
        await self.sdk.hwid.delete_all_hwid_user(body=request)


    async def create_user(self, username: str, tg_id: str, month: int | None = 0, days: int | None = 0, traffic: int | None = None, device_limit: int | None = None) -> str:
        """Создаёт подписку и возвращает её url"""
        end_date = datetime.now(timezone.utc) + timedelta(days=30*month) + timedelta(days=days)
        squad_uuid = 'ba78e6e0-a2db-49d4-9c0d-2320d9a8aad4'
        res_user = username
        i = 1

        # проверяем существует ли уже пользователь с таким именем, если да - добавляем цифру в конце, пока не найдём свободное имя
        while True:
            try:
                await self.sdk.users.get_user_by_username(username=res_user)
                res_user = f"{username}{i}"
                i += 1
            except NotFoundError:
                break

        description = ''
        if month < 1:
            description = "Пробная подписка"

        traffic = traffic * 1024 * 1024 * 1024 if traffic is not None else None

        new_user = await self.sdk.users.create_user(
            CreateUserRequestDto(
                username=res_user,
                telegram_id=str(tg_id),
                expire_at=end_date,
                description=description,
                active_internal_squads=[str(squad_uuid)],
                traffic_limit_strategy="MONTH",
                traffic_limit_bytes=traffic,
                hwid_device_limit=device_limit
            )
        )
        return f'<code>{new_user.subscription_url}</code>'


    async def update_user(self, uuid: str, month: int | None = 0, days: int | None = 0, traffic: int | None = None, device_limit: int | None = None) -> str:
        """Обновляет подписку по её {uuid} на {month} месяцев и возвращает её название"""
        user = await self.sdk.users.get_user_by_uuid(uuid=uuid)

        traffic = traffic * 1024 * 1024 * 1024 if traffic is not None else None

        global_limit = await self.sdk.subscriptions_settings.get_settings()
        device_limit = device_limit if device_limit == 0 else global_limit.hwid_settings.fallback_device_limit

        # проверяем, истекла ли подписка
        if user.expire_at < datetime.now(timezone.utc):
            new_expire = datetime.now(timezone.utc) + timedelta(days=30*month) + timedelta(days=days)
        else:
            new_expire = user.expire_at + timedelta(days=30*month) + timedelta(days=days)

        await self.sdk.users.update_user(
            UpdateUserRequestDto(
                uuid=uuid,
                expire_at=new_expire,
                traffic_limit_strategy="MONTH",
                traffic_limit_bytes=traffic,
                hwid_device_limit=device_limit
            )
        )
        return user.username


remna = Remnawave(
    token=config.remnawave.token,
    panel_url=config.remnawave.panel_url,
    hwid_limit=None
)