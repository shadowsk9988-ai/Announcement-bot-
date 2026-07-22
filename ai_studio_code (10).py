import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import db
from middlewares import RegistrationMiddleware
from handlers import start, groups, broadcast, stats, help

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Initialize Database
    await db.setup()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Middlewares
    dp.update.outer_middleware(RegistrationMiddleware())

    # Routers
    dp.include_router(start.router)
    dp.include_router(groups.router)
    dp.include_router(broadcast.router)
    dp.include_router(stats.router)
    dp.include_router(help.router)

    logging.info("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")