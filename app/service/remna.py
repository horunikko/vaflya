import logging
from datetime import datetime, timedelta, timezone
from remnawave import RemnawaveSDK
from remnawave.models import CreateUserBodyDto, UpdateUserBodyDto, DeleteUserAllHwidDeviceRequestDto, UserResponseDto
from remnawave.exceptions.general import NotFoundError

from config import config
from database.db import database

from handlers.misc import UserStats

logger = logging.getLogger(__name__)


INF = '<tg-emoji emoji-id="5271934788037517525">♾️</tg-emoji>'

def _emoji(emoji_id: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


def _to_gb(value: int) -> float:
    return round(value / 1024 ** 3, 2)


class Remnawave:
    def __init__(self, token, panel_url):
        self.token = token
        self.panel_url = panel_url
        self.hwid_limit = None

        self.sdk = RemnawaveSDK(base_url=self.panel_url, token=self.token)


    async def expire_day(self, notify_days: list[int], end_notify: bool = False) -> list[str]:
        """Возвращает список из telegram id пользователей, чья подписка истекает через {days} дней"""
        start = 0
        notify_days = sorted(notify_days + [0]) if end_notify else sorted(notify_days)

        result: dict[int, list[dict[str, str]]] = {day: [] for day in notify_days}
        now = datetime.now(timezone.utc)
        
        while True:
            response = await self.sdk.users.get_all_users(size=25, start=start)
            if not response.users:
                break
            
            for user in response.users:
                if not user.telegram_id:
                    continue

                sub_days = await database.notifications.get_days(user.username)
                final_day = None
                
                for day in notify_days:
                    if now + timedelta(days=day) >= user.expire_at:
                        final_day = day
                        break
                
                if final_day is not None and (sub_days is None or final_day < sub_days):
                    result[day].append({"tg_id": user.telegram_id, "username": user.username})
                    await database.notifications.create_or_update(username=user.username, notify_days=final_day)

            start += 25
        
        return result


    async def _get_hwid_limit(self):
        """Глобальный лимит устройств"""
        if self.hwid_limit is None:
            settings = (await self.sdk.subscriptions_settings.get_settings()).hwid_settings
            self.hwid_limit = settings.fallback_device_limit if settings.enabled else 0
        return self.hwid_limit


    async def _text_user_stats(self, user: UserResponseDto) -> UserStats:
        """Формирует и возвращает текст с информацией о подписке по его id и hwid"""
        global_hwid_limit = await self._get_hwid_limit()
        hwid = await self.sdk.hwid.get_hwid_user(user_id=str(user.id))
        
        if user.hwid_device_limit == 0:
            devices = INF
        elif user.hwid_device_limit is None:
            devices = global_hwid_limit
        else:
            devices = user.hwid_device_limit

        is_active = user.status.lower() == 'active'
        status = _emoji("5260342697075416641", "✅") if is_active else _emoji("5260342697075416641", "❌")

        expire_time = INF if user.expire_at.year >= 2099 else user.expire_at.strftime('%d.%m.%Y')

        text = (
            f"{status} {user.username}\n"
            "<blockquote expandable>"
            f'{_emoji("5260730055880876557", "🔗")} Ссылка на подписку: '
            f'<code>{user.subscription_url}</code> <i>(нажмите, чтобы скопировать)</i>\n\n'

            f'{_emoji("5199457120428249992", "📆")} Дата истечения подписки: {expire_time}\n\n'

            f'{_emoji("5258508428212445001", "📱")} Количество устройств: <b>{int(hwid.total)}</b>/{devices}\n\n'

            f'{_emoji("5258330865674494479", "⚡️")} Трафик <i>(месяц/всё время)</i>: '
            f'<b>{_to_gb(user.used_traffic_bytes)}ГБ / {_to_gb(user.lifetime_used_traffic_bytes)}ГБ</b>'
            "</blockquote>\n\n"
        )

        return UserStats(
            username=user.username,
            rw_id=user.id,
            expire_time=expire_time,
            devices=devices,
            text=text
        )


    async def user_stats(self, tg_id: str | int | None = None, username: str | None = None) -> list[str] | None:
        """Функция получения статистики по tg_id или id.
        Возвращает список из инфы о всех подписках по тг айди или инфу о подписке по id"""
        if username:
            users = [await self.sdk.users.get_user_by_username(username=username)]

        if tg_id:
            responce = await self.sdk.users.get_users_stream(telegram_id=str(tg_id)) 
            users = responce.users

        res: list[UserStats] = []
        for user in users:
            res.append(await self._text_user_stats(user))

        return res
        

    async def user_name(self, tg_id: str | int) -> dict[str, str]:
        """Возвращает список значений username всех подписок по tg_id"""
        responce = await self.sdk.users.get_users_stream(telegram_id=str(tg_id))
        return [user.username for user in responce.users]


    async def delete_devices(self, rw_id: str) -> None:
        """Сбрасывает все устройства для подписки"""
        await self.sdk.hwid.delete_all_hwid_user(
            body=DeleteUserAllHwidDeviceRequestDto(
                user_id=rw_id
            )
        )


    async def create_user(self, 
        username: str, 
        tg_id: str, 
        month: int | None = 0, 
        days: int | None = 0, 
        traffic: int | None = None, 
        device_limit: int | None = None
    ) -> str:
        """Создаёт подписку и возвращает её url"""
        end_date = datetime.now(timezone.utc) + timedelta(days=30*month) + timedelta(days=days)
        if username.isdigit():
            username = 'tg' + username
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

        traffic = traffic * 1024 * 1024 * 1024 if traffic is not None else None

        new_user = await self.sdk.users.create_user(
            CreateUserBodyDto(
                username=res_user,
                telegram_id=str(tg_id),
                expire_at=end_date,
                active_internal_squads=[config.subscription.base_squad_uuid],
                traffic_limit_strategy="MONTH",
                traffic_limit_bytes=traffic,
                hwid_device_limit=device_limit
            )
        )
        return f'<code>{new_user.subscription_url}</code>'


    async def update_user(self, 
        username: str, 
        month: int | None = 0, 
        days: int | None = 0, 
        traffic: int | None = None, 
        device_limit: int | None = None
    ) -> str:
        """Обновляет подписку по её {uuid} на {month} месяцев и возвращает её название"""
        user = await self.sdk.users.get_user_by_username(username=username)

        traffic = traffic * 1024 * 1024 * 1024 if traffic is not None else None

        global_limit = await self.sdk.subscriptions_settings.get_settings()
        device_limit = device_limit if device_limit == 0 else global_limit.hwid_settings.fallback_device_limit

        # проверяем, истекла ли подписка
        if user.expire_at < datetime.now(timezone.utc):
            new_expire = datetime.now(timezone.utc) + timedelta(days=30*month) + timedelta(days=days)
        else:
            new_expire = user.expire_at + timedelta(days=30*month) + timedelta(days=days)

        await self.sdk.users.update_user(
            UpdateUserBodyDto(
                username=username,
                expire_at=new_expire,
                traffic_limit_strategy="MONTH",
                traffic_limit_bytes=traffic,
                hwid_device_limit=device_limit
            )
        )
        return user.username


    async def delete_user(self, username: str) -> str:
        """Удаление сабки пользователя"""
        user = await self.sdk.users.get_user_by_username(username=username)
        await self.sdk.users.delete_user(user.id)
        return user.telegram_id


    async def disable_user(self, rw_id: int) -> str:
        """Отключение сабки пользователя"""
        user = await self.sdk.users.disable_user(rw_id)
        return user.telegram_id, user.username

remna = Remnawave(
    token=config.remnawave.token,
    panel_url=config.remnawave.panel_url
)
