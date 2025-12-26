import logging
import aiosqlite

from aiogram import F
from aiogram.types import Message

from ..database import DB_PATH
from ..config import ADMIN_IDS

logger = logging.getLogger(__name__)


async def cmd_stats(msg: Message):
    logger.info("Stats command from user %s", msg.from_user.id if msg.from_user else "unknown")
    
    if not msg.from_user:
        return
    
    if msg.from_user.id not in ADMIN_IDS:
        logger.info("User %s not in ADMIN_IDS %s", msg.from_user.id, ADMIN_IDS)
        return
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Всего сообщений
        cur = await db.execute("SELECT COUNT(*) FROM messages")
        row = await cur.fetchone()
        total_messages = row[0] if row else 0
        
        # Сообщений за сегодня
        cur = await db.execute(
            "SELECT COUNT(*) FROM messages WHERE DATE(created_at) = DATE('now')"
        )
        row = await cur.fetchone()
        today_messages = row[0] if row else 0
        
        # Уникальных отправителей
        cur = await db.execute(
            "SELECT COUNT(DISTINCT sender_user_id) FROM messages WHERE sender_user_id IS NOT NULL"
        )
        row = await cur.fetchone()
        unique_senders = row[0] if row else 0
        
        # Заблокированных пользователей
        cur = await db.execute("SELECT COUNT(*) FROM blocked_users")
        row = await cur.fetchone()
        blocked_count = row[0] if row else 0
        
        # Всего ссылок
        cur = await db.execute("SELECT COUNT(*) FROM links")
        row = await cur.fetchone()
        total_links = row[0] if row else 0
        
        # Всего пользователей
        cur = await db.execute("SELECT COUNT(*) FROM users")
        row = await cur.fetchone()
        total_users = row[0] if row else 0
    
    await msg.answer(
        "📊 <b>Статистика бота</b>\n\n"
        f"📨 Сообщений всего: <b>{total_messages}</b>\n"
        f"📅 Сообщений сегодня: <b>{today_messages}</b>\n"
        f"👥 Уникальных отправителей: <b>{unique_senders}</b>\n"
        f"🔗 Ссылок создано: <b>{total_links}</b>\n"
        f"👤 Пользователей: <b>{total_users}</b>\n"
        f"🚫 Заблокировано: <b>{blocked_count}</b>",
        parse_mode="HTML"
    )


def register_handlers(dp):
    dp.message.register(cmd_stats, F.text == "/stats")
