from database.db import get_db

async def create_user(
    telegram_id: int,
    username: str | None,
    referral_from: str | None,
    referral_code: str
):

    db = await get_db()

    await db.execute("""

    INSERT OR IGNORE INTO users (

        telegram_id,
        username,
        referral_from,
        referral_code

    )

    VALUES (?, ?, ?, ?)

    """, (

        telegram_id,
        username,
        referral_from,
        referral_code

    ))

    await db.commit()
    await db.close()

async def activate_trial(telegram_id: int):

    db = await get_db()

    await db.execute("""

    UPDATE users

    SET trial_activated = 1

    WHERE telegram_id = ?

    """, (

        telegram_id,

    ))

    await db.commit()

    await db.close()

async def has_trial(telegram_id: int) -> bool:

    db = await get_db()

    async with db.execute("""

    SELECT trial_activated

    FROM users

    WHERE telegram_id = ?

    """, (

        telegram_id,

    )) as cursor:

        row = await cursor.fetchone()

    await db.close()

    return bool(row[0]) if row else False