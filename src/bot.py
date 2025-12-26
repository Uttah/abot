import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from .config import BOT_TOKEN, REDIS_URL
from .database import init_db, migrate_db

from .handlers.start import register_handlers as register_start
from .handlers.stop import register_handlers as register_stop
from .handlers.anon_message import register_handlers as register_anon
from .handlers.reply_click import register_handlers as register_reply_click
from .handlers.owner_reply import register_handlers as register_owner_reply
from .handlers.block import register_handlers as register_block
from .handlers.debug import register_handlers as register_debug
from .handlers.errors import router as errors_router
from .middlewares.throttling import ThrottlingMiddleware


async def main():
    logging.basicConfig(level=logging.INFO)

    await init_db()
    await migrate_db()

    redis = Redis.from_url(REDIS_URL)
    storage = RedisStorage(redis=redis)
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=storage)
    
    # Rate limiting middleware
    dp.message.middleware(ThrottlingMiddleware())

    await bot.set_my_commands([
        BotCommand(command="start",
                   description="Запустить бота или задать вопрос"),
        BotCommand(command="stop",
                   description="Завершить сессию анонимных сообщений"),
    ])

    register_start(dp)
    register_stop(dp)
    register_anon(dp)
    register_reply_click(dp)
    register_owner_reply(dp)
    register_block(dp)
    register_debug(dp)
    
    # Регистрируем обработчик ошибок
    dp.include_router(errors_router)

    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await redis.close()

if __name__ == "__main__":
    asyncio.run(main())
