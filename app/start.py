import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiohttp import web

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logging.getLogger("aiogram").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


from handlers.menu import push
from database.db import database
from payment.webhook import yookassa_webhook
from config import config


bot = Bot(token=config.telegram.token)
dp = Dispatcher()


from handlers import menu, info, sub, admin, referral
for router in (menu.router, info.router, sub.router, admin.router, referral.router):
    dp.include_router(router)



async def start_webhook(bot):
    app = web.Application()
    app["bot"] = bot

    app.router.add_post("/yookassa/webhook", yookassa_webhook)
    runner = web.AppRunner(app)

    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 8080)
    await site.start()


async def main():
    dp["bot_info"] = await bot.get_me()
    await database.init_db()

    asyncio.create_task(push(bot))
    await start_webhook(bot)

    logger.info('Включение бота')

    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Выключение бота...")