import os
import logging
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()
logger = logging.getLogger(__name__)


def require_value(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"Обязательный параметр {name} не указан. Укажите его в файле .env")

    return value


def prefer_value(name: str) -> str:
    value = os.getenv(name)

    if not value:
        logger.info(f"Необязательный параметр {name} не указан")

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
    support_link: str
    channel_link: str

    info_active: bool | None = None
    instruction_active: bool | None = None
    admin_ids: str | None = None
    proxy: str | None = None


@dataclass(frozen=True)
class RemnaConfig():
    """Конфиг ремны"""
    token: str
    sub_domain: str
    panel_url: str


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
    active: bool | None = None
    inn: str | None = None
    password: str | None = None
    proxy: str | None = None


tg_config = TgConfig(
    token=require_value("TG_TOKEN"),
    support_link=require_value("TG_SUPPORT_LINK"),
    channel_link=require_value("TG_CHANNEL_LINK"),
    info_active=bool(prefer_value("TG_INFO")),
    instruction_active=bool(prefer_value("TG_INSTRUCTION")),
    admin_ids=prefer_value("TG_ADMIN_IDS"),
    proxy=prefer_value("TG_PROXY"),
)


remna_config = RemnaConfig(
    token=require_value("REMNA_TOKEN"),
    sub_domain=require_value("REMNA_SUB_DOMAIN"),
    panel_url=require_value("REMNA_PANEL_URL"),
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