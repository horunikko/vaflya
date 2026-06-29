import aiosqlite
from .payment import Payment
from .users import Users
from .notifications import Notification


class Database:
    """Класс конфига базы данных"""
    def __init__(self, path: str):
        self.path = path

        self.payment = Payment(self)
        self.users = Users(self)
        self.notifications = Notification(self)


    async def init_db(self) -> None:
        """Инициализация бд"""
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                referral_from TEXT,
                referral_code TEXT UNIQUE,
                referral_count INTEGER DEFAULT 0,
                has_payed_sub INTEGER
            )
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                processed INTEGER DEFAULT 0
            )
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                uuid TEXT PRIMARY KEY,
                notify_days INTEGER
            )
            """)
            await db.commit()


database = Database("app/database/database.db")