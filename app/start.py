import asyncio
from aiogram import Bot, Dispatcher
from config import config as vaflya_config
from handlers.menu import push
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logging.getLogger("aiogram").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


bot = Bot(token=vaflya_config.tg_token)
dp = Dispatcher()


# роутеры
from handlers import menu, info, pay, sub, admin
for router in (menu.router, info.router, pay.router, sub.router, admin.router):
    dp.include_router(router)


async def main():
    logger.info('Запуск бота...')
    
    bot_info = await bot.get_me()
    dp["bot_info"] = bot_info

    asyncio.create_task(push(bot))
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Выключение бота...")