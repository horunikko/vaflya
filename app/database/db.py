import aiosqlite

DB_PATH = "app/database/database.db"


async def get_db():
    return await aiosqlite.connect(DB_PATH)


async def init_db() -> None:
    """Инициализация бд"""
    async with aiosqlite.connect(DB_PATH) as db:
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
            status TEXT NOT NULL,
            processed INTEGER DEFAULT 0
        )
        """)

        await db.commit()