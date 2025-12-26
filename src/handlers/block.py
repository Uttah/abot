import aiosqlite

from aiogram.types import CallbackQuery, Message

from ..callbacks import BlockCallback
from ..database import DB_PATH


async def on_block_click(cb: CallbackQuery, callback_data: BlockCallback):
    """Обработчик нажатия кнопки 'Заблокировать'."""
    message_id = callback_data.message_id
    
    if not cb.from_user:
        await cb.answer("Ошибка", show_alert=True)
        return
    
    owner_tg_id = cb.from_user.id
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Получаем owner_id и sender_user_id из сообщения
        cur = await db.execute(
            """
            SELECT m.sender_user_id, l.owner_id 
            FROM messages m
            JOIN links l ON l.id = m.link_id
            WHERE m.id = ?
            """,
            (message_id,)
        )
        row = await cur.fetchone()
        
        if not row:
            await cb.answer("❌ Сообщение не найдено", show_alert=True)
            return
        
        sender_user_id, owner_id = row
        
        if not sender_user_id:
            await cb.answer("❌ Отправитель неизвестен", show_alert=True)
            return
        
        # Проверяем что нажавший — владелец ссылки
        cur = await db.execute(
            "SELECT id FROM users WHERE tg_user_id = ?",
            (owner_tg_id,)
        )
        owner_row = await cur.fetchone()
        
        if not owner_row or owner_row[0] != owner_id:
            await cb.answer("❌ Вы не можете заблокировать этого пользователя", show_alert=True)
            return
        
        # Проверяем, не заблокирован ли уже
        cur = await db.execute(
            "SELECT id FROM blocked_users WHERE owner_id = ? AND blocked_id = ?",
            (owner_id, sender_user_id)
        )
        if await cur.fetchone():
            await cb.answer("ℹ️ Этот пользователь уже заблокирован", show_alert=True)
            return
        
        # Блокируем
        await db.execute(
            "INSERT INTO blocked_users (owner_id, blocked_id) VALUES (?, ?)",
            (owner_id, sender_user_id)
        )
        await db.commit()
    
    await cb.answer("✅ Пользователь заблокирован. Он больше не сможет отправлять вам сообщения.", show_alert=True)
    
    # Обновляем клавиатуру — убираем кнопки
    if cb.message and isinstance(cb.message, Message):
        await cb.message.edit_reply_markup(reply_markup=None)


def register_handlers(dp):
    dp.callback_query.register(on_block_click, BlockCallback.filter())
