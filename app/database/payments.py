from database.db import get_db



async def create_payment_record(payment_id: str) -> None:
    """Создаёт запись в бд при создании платежа пользователем"""
    db = await get_db()

    await db.execute("""
        INSERT OR IGNORE INTO payments (payment_id, status)
        VALUES (?, ?)
    """, (payment_id, "pending"))

    await db.commit()
    await db.close()


async def is_payment_processed(payment_id: str) -> bool:
    """Возвращает True если платёж уже прошёл.
    Нужно для предотвращения повторной выдачи/продления подписки"""
    db = await get_db()

    async with db.execute("""
        SELECT processed
        FROM payments
        WHERE payment_id = ?
    """, (payment_id,)) as cursor:
        row = await cursor.fetchone()
    
    await db.close()
    return bool(row and row[0])


async def mark_payment_processed(payment_id: str) -> None:
    """Помечает платёж выполненным"""
    db = await get_db()
    await db.execute("""
        UPDATE payments
        SET processed = 1
        WHERE payment_id = ?
    """, (payment_id,))

    await db.commit()
    await db.close()


async def update_payment_status(payment_id: str, status: str) -> None:
    """Обновляет статус платежа. Ни ебу зачем, удалю потом если не нужно будет"""
    db = await get_db()
    await db.execute("""
        UPDATE payments
        SET status = ?
        WHERE payment_id = ?
    """, (status, payment_id))

    await db.commit()
    await db.close()