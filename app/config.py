import os
import logging
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()
logger = logging.getLogger(__name__)


def require_value(name: str) -> str:
    value = os.getenv(name).strip()

    if not value:
        raise RuntimeError(f"Обязательный параметр {name} не указан. Укажите его в файле .env")

    return value


def prefer_value(name: str, is_int: bool = False) -> str:
    value = os.getenv(name).strip()

    if not value:
        if name == 'YOOKASSA_RETURN_URL':
            logger.info(f"{name} не указан, используем дефолтный")
        else:
            logger.info(f"Необязательный параметр {name} не указан, не используем его")
        if is_int:
            return 0
        return None

    if is_int:
        return int(value)
    
    return value


nalogo_active = os.getenv("NALOGO_ACTIVE")
nalogo_inn = os.getenv("NALOGO_INN")
nalogo_password = os.getenv("NALOGO_PASSWORD")

if nalogo_active and not (nalogo_inn or nalogo_password):
    raise RuntimeError(
        "Отсутствует ИНН или пароль! Отключите формирование чеков или укажите ИНН или пароль!"
    )


@dataclass(frozen=True)
class TgConfig():
    """Конфиг телеграмма"""
    token: str
    support_link: str | None
    channel_link: str | None

    privacy_url: str | None
    terms_url: str | None

    admin_ids: str | None
    proxy: str | None
    notify_days: list | None


@dataclass(frozen=True)
class RemnaConfig():
    """Конфиг ремны"""
    token: str
    panel_url: str


@dataclass(frozen=True)
class SubConfig():
    """Конфиг подписок"""
    base_traffic: int | None
    base_devices: int | None

    trial_days: int | None
    trial_traffic: int | None
    trial_devices: int | None

    ref_bonus_days: int | None


@dataclass(frozen=True)
class PaymentConfig():
    """Конфиг платёжки и цен"""
    # юкасса
    shop_id: str
    secret_key: str

    # цены
    one_month: int
    three_month: int
    one_year: int

    # необязательный параметр
    return_url: str | None


@dataclass(frozen=True)
class NalogoConfig():
    """Конфиг налоговой"""
    active: bool | None
    inn: str | None
    password: str | None
    proxy: str | None


tg_config = TgConfig(
    token=require_value("TG_TOKEN"),
    support_link=prefer_value("TG_SUPPORT_LINK"),
    channel_link=prefer_value("TG_CHANNEL_LINK"),

    privacy_url=prefer_value("TG_PRIVACY_URL"),
    terms_url=prefer_value("TG_TERMS_URL"),

    admin_ids=prefer_value("TG_ADMIN_IDS"),
    proxy=prefer_value("TG_PROXY"),
    notify_days=prefer_value("TG_NOTIFY_DAYS")
)


remna_config = RemnaConfig(
    token=require_value("REMNA_TOKEN"),
    panel_url=require_value("REMNA_PANEL_URL"),
)


base_traffic = prefer_value("SUB_BASE_TRAFFIC", is_int=True)
base_devices = prefer_value("SUB_BASE_DEVICES", is_int=True)


sub_config = SubConfig(
    base_traffic=base_traffic,
    base_devices=base_devices or None,

    trial_days=prefer_value("SUB_TRIAL_DAYS", is_int=True) or 5,
    trial_traffic=prefer_value("SUB_TRIAL_TRAFFIC", is_int=True) or base_traffic,
    trial_devices=prefer_value("SUB_TRIAL_DEVICES", is_int=True) or base_devices,
    ref_bonus_days=prefer_value("SUB_REF_BONUS_DAYS", is_int=True)
)


payment_config = PaymentConfig(
    shop_id=require_value("YOOKASSA_SHOP_ID"),
    secret_key=require_value("YOOKASSA_SECRET_KEY"),

    one_month=int(require_value("ONE_MONTH")),
    three_month=int(require_value("THREE_MONTHS")),
    one_year=int(require_value("ONE_YEAR")),

    return_url=prefer_value("YOOKASSA_RETURN_URL")
)


nalogo_config = NalogoConfig(
    active=bool(prefer_value("NALOGO_ACTIVE")),
    inn=prefer_value("NALOGO_INN"),
    password=prefer_value("NALOGO_PASSWORD"),
    proxy=prefer_value("NALOGO_PROXY")
)