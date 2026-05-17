import aiosqlite
import base64


class Database:
    """Класс конфига базы данных"""
    def __init__(self, db_path: str):
        self.db_path = db_path


    async def init_db(self) -> None:
        """Инициализация бд"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                referral_from TEXT,
                referral_code TEXT UNIQUE,
                trial_activated INTEGER DEFAULT 0
            )
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                processed INTEGER DEFAULT 0
            )
            """)

            await db.commit()


    async def create_payment_record(self, payment_id: str) -> None:
        """Создаёт запись в бд при создании платежа пользователем"""
        async with aiosqlite.connect(self.db_path) as db:

            await db.execute("""
                INSERT OR IGNORE INTO payments (payment_id)
                VALUES (?)
            """, (payment_id,))

            await db.commit()


    async def is_payment_processed(self, payment_id: str) -> bool:
        """Возвращает True если платёж уже прошёл.
        Нужно для предотвращения повторной выдачи/продления подписки"""
        async with aiosqlite.connect(self.db_path) as db:

            async with db.execute("""
                SELECT processed
                FROM payments
                WHERE payment_id = ?
            """, (payment_id,)) as cursor:
                row = await cursor.fetchone()
            
            return bool(row and row[0])


    async def mark_payment_processed(self, payment_id: str) -> None:
        """Помечает платёж выполненным"""
        async with aiosqlite.connect(self.db_path) as db:

            await db.execute("""
                UPDATE payments
                SET processed = 1
                WHERE payment_id = ?
            """, (payment_id,))

            await db.commit()

        
    def gen_ref_code(self, tg_id: int | str) -> str: 
        """Генерация уникальных реферальных кодов на основе tg_id""" 
        return base64.urlsafe_b64encode(str(tg_id).encode()).decode().rstrip("=")


    async def create_user(self, tg_id: int, username: str | None = None, referral_from: str | None = None):
        """Создаёт запись о пользователе в бд, либо обновляет его"""
        async with aiosqlite.connect(self.db_path) as db:

            await db.execute("""
            INSERT INTO users (
                telegram_id,
                username,
                referral_from,
                referral_code
            )
            VALUES (?, ?, ?, ?)

            ON CONFLICT(telegram_id) DO UPDATE SET
                username=excluded.username,
                referral_from = COALESCE(
                    excluded.referral_from,
                    users.referral_from
                )
            """, (
                tg_id,
                username,
                referral_from,
                self.gen_ref_code(tg_id)
            ))

            await db.commit()

    async def activate_trial(self, telegram_id: int):
        """Делает запись в поле пользователя об активации пробного периода"""
        async with aiosqlite.connect(self.db_path) as db: 

            await db.execute("""
                UPDATE users 
                SET trial_activated = 1 
                WHERE telegram_id = ? """,
                (telegram_id,))
            
            await db.commit()
        
    async def has_trial(self, telegram_id: int) -> bool: 
        """Возвращает True, если у пользователя уже был пробный период"""
        async with aiosqlite.connect(self.db_path) as db:

            async with db.execute(""" 
                SELECT trial_activated 
                FROM users WHERE 
                telegram_id = ? """, 
            (telegram_id,)) as cursor:
                
                row = await cursor.fetchone()
                return bool(row[0]) if row else False


database = Database("app/database/database.db")