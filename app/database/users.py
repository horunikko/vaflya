import aiosqlite
import base64


class Users:
    def __init__(self, database):
        self.database = database


    def gen_ref_code(self, tg_id: int | str) -> str: 
        """Генерация уникальных реферальных кодов на основе tg_id через base64""" 
        return base64.urlsafe_b64encode(str(tg_id).encode()).decode().rstrip("=")

    
    async def create(
        self,
        tg_id: int, 
        username: str | None = None, 
        referral_from: str | None = None,
        has_user_sub: int | None = None
    ):
        """Создаёт запись о пользователе в бд, либо обновляет его"""
        async with aiosqlite.connect(self.database.path) as db:

            await db.execute("""
            INSERT INTO users (
                telegram_id,
                username,
                referral_code,
                referral_from,
                has_payed_sub
            )
            VALUES (?, ?, ?, ?, ?)

            ON CONFLICT(telegram_id) DO UPDATE SET
                username=excluded.username,
                referral_from=COALESCE( 
                    excluded.referral_from, 
                    users.referral_from
                ),
                has_payed_sub=COALESCE(
                    excluded.has_payed_sub,
                    users.has_payed_sub
                )
                """, (
                tg_id,
                username,
                self.gen_ref_code(tg_id),
                referral_from,
                has_user_sub
            ))

            await db.commit()


    async def get_user(self, telegram_id: int) -> dict | None:
        """Возвращает данные пользователя по telegram_id"""
        async with aiosqlite.connect(self.database.path) as db:

            db.row_factory = aiosqlite.Row

            async with db.execute("""
                SELECT
                    telegram_id,
                    username,
                    referral_from,
                    referral_code,
                    referral_count,
                    has_payed_sub
                FROM users
                WHERE telegram_id = ?
            """, (telegram_id,)) as cursor:

                row = await cursor.fetchone()

                return dict(row) if row else None


    async def activate_sub(self, telegram_id: int):
        """Делает запись в поле пользователя о получении первой платной подписки"""
        async with aiosqlite.connect(self.database.path) as db:

            await db.execute("""
                UPDATE users
                SET has_payed_sub = 1
                WHERE telegram_id = ?
                """,
                (telegram_id,))
            
            await db.commit()

        
    async def has_payed_sub(self, telegram_id: int) -> bool: 
        """Возвращает True, если у пользователя была/есть платная подписка"""
        async with aiosqlite.connect(self.database.path) as db:

            async with db.execute(""" 
                SELECT has_payed_sub
                FROM users WHERE 
                telegram_id = ? """, 
            (telegram_id,)) as cursor:
                
                row = await cursor.fetchone()
                return bool(row[0]) if row else False
            

    async def referral_from_by_ref_code(self, referral_code: str) -> int | None:
        """Возвращает telegram_id владельца referral_code"""
        async with aiosqlite.connect(self.database.path) as db:

            async with db.execute("""
                SELECT telegram_id
                FROM users
                WHERE referral_code = ?
            """, (referral_code,)) as cursor:

                row = await cursor.fetchone()

                return row[0] if row else None


    async def referral_from(self, telegram_id: int) -> int | None:
        """Возвращает referral_from по telegram_id"""
        async with aiosqlite.connect(self.database.path) as db:

            async with db.execute("""
                SELECT referral_from
                FROM users
                WHERE telegram_id = ?
            """, (telegram_id,)) as cursor:

                row = await cursor.fetchone()

                return row[0] if row else None
            

    async def update_ref_count(self, telegram_id: int, count: int | None = 1) -> None:
        """Обновляет количество пришедших людей по рефке у юзера"""
        async with aiosqlite.connect(self.database.path) as db:

            await db.execute("""
                UPDATE users
                SET referral_count = referral_count + ?
                WHERE telegram_id = ?
                """,
                (count, telegram_id))
            
            await db.commit()

    
    async def get_username(self, telegram_id: str) -> int | None:
        """Возвращает username по telegram_id"""
        async with aiosqlite.connect(self.database.path) as db:

            async with db.execute("""
                SELECT username
                FROM users
                WHERE telegram_id = ?
            """, (telegram_id,)) as cursor:

                row = await cursor.fetchone()

                return row[0] if row else None

    
    async def get_telegram_id(self, username: str) -> int | None:
        """Возвращает telegram_id по username"""
        async with aiosqlite.connect(self.database.path) as db:

            async with db.execute("""
                SELECT telegram_id
                FROM users
                WHERE username = ?
            """, (username,)) as cursor:

                row = await cursor.fetchone()

                return row[0] if row else None
            

    async def delete_user(self, telegram_id: int) -> None:
        async with aiosqlite.connect(self.database.path) as db:
            await db.execute(
                "DELETE FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            await db.commit()