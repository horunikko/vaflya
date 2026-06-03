from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, HttpUrl, AnyUrl, model_validator, Field, BaseModel

class Telegram(BaseSettings):
    token: str

    support_link: HttpUrl | None = None
    channel_link: HttpUrl | None = None

    admin_ids: list[int] | None = None

    proxy: AnyUrl | None = None

    notify_days: list[int] | None = None

    privacy_url: AnyUrl | None = None
    terms_url: AnyUrl | None = None

    @field_validator('admin_ids', mode='before')
    def list_ids(cls, value):
        if not value:
            return None

        return [int(x) for x in value.strip().split(',')]
    
    @field_validator('channel_link', "support_link", "proxy", mode='before')
    def tg_link(cls, value: str | None):
        if not value:
            return None
        
        if value.startswith('https://') or value.startswith('tg://'):
            return value
        
        if 't.me' in value:
            return f'https://{value}'
        
        return f'https://t.me/{value.removeprefix("@")}'
    

    @field_validator('privacy_url', 'terms_url', mode='before')
    def to_link(cls, value: str | None):
        if not value:
            return None
        
        if '.' not in value:
            raise ValueError(f"Неправильный формат ссылки {value} !")
        
        if value.startswith('https://'):
            return value
        
        return f'https://{value}'

    
    @field_validator('notify_days', mode='before')
    def notify_range(cls, value: str | None):
        if not value:
            return

        result = set()

        for part in str(value).split(","):
            part = part.strip()

            if not part:
                continue

            if "-" in part:
                start, end = map(int, part.split("-", 1))

                if start > end:
                    raise ValueError(f"Некорректный диапазон TG_NOTIFY_DAYS: {part}")

                result.update(range(start, end + 1))
            else:
                result.add(int(part))

        return sorted(result)


    @field_validator('support_link', 'channel_link', 'privacy_url', 'terms_url', mode='after')
    def url_to_str(cls, value):
        if not value:
            return
        return str(value)
    

    model_config = SettingsConfigDict(
        env_prefix='TG_',
        env_file='.env',
        extra="ignore"
    )


class Remnawave(BaseSettings):
    token: str
    panel_url: HttpUrl

    @field_validator('panel_url', mode='after')
    def url_check(cls, value: HttpUrl):
        scheme = value.scheme

        is_local = any(x in value.host for x in ('127.0.0.', 'localhost', '0.0.0.'))

        if scheme == 'https' and is_local:
            raise ValueError('Локальные адреса должны использовать http://')

        return value


    @field_validator('panel_url', mode='after')
    def url_to_str(cls, value):
        if not value:
            return
        return str(value)
            

    model_config = SettingsConfigDict(
        env_prefix='REMNAWAVE_',
        env_file='.env',
        extra="ignore"
    )


class Subscription(BaseSettings):
    base_traffic: int = 0
    trial_traffic: int | None = None

    base_devices: int = 0
    trial_devices: int | None = None

    trial_days: int = 0

    ref_bonus_days: int = 0


    @field_validator('base_traffic', 'base_devices', 'trial_days', 'ref_bonus_days', mode='before')
    def empty_to_zero(cls, value: str | None):
        return 0 if not value or value.strip() == "" else value


    @field_validator('trial_traffic', 'trial_devices', mode='before')
    def empty_to_none(cls, value: str | None):
        if value != "0" and not value:
            return None
        return value


    @model_validator(mode='after')
    def empty_to_base(self):
        if self.trial_traffic is None:
            self.trial_traffic = self.base_traffic

        if self.trial_devices is None:
            self.trial_devices = self.base_devices

        return self

    model_config = SettingsConfigDict(
        env_prefix='SUB_',
        env_file='.env',
        extra="ignore"
    )


class Yookassa(BaseSettings):
    shop_id: int
    secret_key: str
    return_url: AnyUrl | None = None

    @field_validator('return_url', mode='before')
    def empty_to_none(cls, value):
        if not value:
            return None
        return value

    @field_validator('return_url', mode='after')
    def url_to_str(cls, value):
        if not value:
            return
        return str(value)

    model_config = SettingsConfigDict(
        env_prefix='YOOKASSA_',
        env_file='.env',
        extra="ignore"
    )


class Price(BaseSettings):
    one: int = Field(ge=10)
    three: int = Field(ge=10)
    twelve: int = Field(ge=10)

    model_config = SettingsConfigDict(
        env_prefix='PRICE_',
        env_file='.env',
        extra="ignore"
    )


class Nalogo(BaseSettings):
    active: bool = False
    inn: int | None = None
    password: str | None = None
    proxy: str | None = None


    @field_validator('active', mode='before')
    def empty_to_false(cls, value: str | None):
        if not value:
            return False
        return value

    @field_validator('inn', 'password', 'proxy', mode='before')
    def empty_to_none(cls, value: str | None):
        if not value:
            return None
        return value


    @model_validator(mode="after")
    def validate_active(self):
        if self.active:
            if self.inn is None:
                raise ValueError("Укажите NALOGO_INN")

            if not self.password:
                raise ValueError("Укажите NALOGO_PASSWORD")
            
        return self

    model_config = SettingsConfigDict(
        env_prefix='NALOGO_',
        env_file='.env',
        extra="ignore"
    )


class Config(BaseModel):
    telegram: Telegram = Telegram()
    remnawave: Remnawave = Remnawave()
    subscription: Subscription = Subscription()
    yookassa: Yookassa = Yookassa()
    price: Price = Price()
    nalogo: Nalogo = Nalogo()



config = Config()