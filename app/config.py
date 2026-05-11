from dataclasses import dataclass
import os
import logging
from dotenv import load_dotenv

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
class Config():
    # тг
    tg_token: str
    tg_support_link: str
    tg_channel_link: str

    # ремна
    remna_token: str
    remna_sub_domain: str
    remna_panel_url: str

    # юкасса
    yookassa_token: str

    # цены
    one_month: int
    three_month: int
    one_year: int

    # необязательные параметры
    # тг
    tg_info: bool | None = None
    tg_instruction: bool | None = None
    tg_admin_ids: str | None = None
    tg_proxy: str | None = None

    # nalogo
    nalogo_active: bool | None = None
    nalogo_inn: str | None = None
    nalogo_password: str | None = None
    nalogo_proxy: str | None = None


config = Config(
    tg_token=require_value("TG_TOKEN"),
    tg_support_link=require_value("TG_SUPPORT_LINK"),
    tg_channel_link=require_value("TG_CHANNEL_LINK"),
    tg_info=bool(prefer_value("TG_INFO")),
    tg_instruction=bool(prefer_value("TG_INSTRUCTION")),
    tg_admin_ids=prefer_value("TG_ADMIN_IDS"),
    tg_proxy=prefer_value("TG_PROXY"),

    remna_token=require_value("REMNA_TOKEN"),
    remna_sub_domain=require_value("REMNA_SUB_DOMAIN"),
    remna_panel_url=require_value("REMNA_PANEL_URL"),

    yookassa_token=require_value("YOOKASSA_TOKEN"),

    one_month=int(require_value("ONE_MONTH")),
    three_month=int(require_value("THREE_MONTHS")),
    one_year=int(require_value("ONE_YEAR")),

    nalogo_active=bool(prefer_value("NALOGO_ACTIVE")),
    nalogo_inn=prefer_value("NALOGO_INN"),
    nalogo_password=prefer_value("NALOGO_PASSWORD"),
    nalogo_proxy=prefer_value("NALOGO_PROXY")
)