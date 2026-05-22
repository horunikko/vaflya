import aiosqlite


class Payment:
    def __init__(self, database):
        self.database = database


    async def record_create(self, payment_id: str) -> None:
        """Создаёт запись в бд при создании платежа пользователем"""
        async with aiosqlite.connect(self.database.path) as db:

            await db.execute("""
                INSERT OR IGNORE INTO payments (payment_id)
                VALUES (?)
            """, (payment_id,))

            await db.commit()


    async def is_processed(self, payment_id: str) -> bool:
        """Возвращает True если платёж уже прошёл.
        Нужно для предотвращения повторной выдачи/продления подписки"""
        async with aiosqlite.connect(self.database.path) as db:

            async with db.execute("""
                SELECT processed
                FROM payments
                WHERE payment_id = ?
            """, (payment_id,)) as cursor:
                row = await cursor.fetchone()
            
            return bool(row and row[0])


    async def mark_processed(self, payment_id: str) -> None:
        """Помечает платёж выполненным"""
        async with aiosqlite.connect(self.database.path) as db:

            await db.execute("""
                UPDATE payments
                SET processed = 1
                WHERE payment_id = ?
            """, (payment_id,))

            await db.commit()