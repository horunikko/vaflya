import aiosqlite


class Notification():
    def __init__(self, database):
        self.database = database

    
    async def create_or_update(self, uuid: str, notify_days: int = 0) -> None:
        """Функция создания/обновления уведомлений об окончании подписки"""
        async with aiosqlite.connect(self.database.path) as db:

            await db.execute("""
                INSERT INTO notifications (
                    uuid,
                    notify_days
                )
                VALUES (?, ?)
                             
                ON CONFLICT(uuid) DO UPDATE SET
                    notify_days=excluded.notify_days
                """, (uuid, notify_days))
            
            await db.commit()

    
    async def get_days(self, uuid: str) -> int | None:
        """Функция получения количества уведомлений у пользователя"""
        async with aiosqlite.connect(self.database.path) as db:

            async with db.execute(""" 
                SELECT notify_days
                FROM notifications WHERE 
                uuid = ? 
            """, (uuid,)) as cursor:
                
                row = await cursor.fetchone()
                return row[0] if row else None