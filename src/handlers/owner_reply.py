import aiosqlite

from aiogram import Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from ..database import DB_PATH
from ..states import Form
from ..media import extract_media, send_media


async def owner_reply(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    orig_msg_id = data.get("reply_message_id")
    
    if not orig_msg_id:
        await state.clear()
        await msg.answer("⚠️ Сессия истекла. Нажмите кнопку 'Ответить' ещё раз.")
        return
    
    if not msg.from_user:
        return

    media_type, file_id, text = extract_media(msg)

    if media_type is None and text is None:
        await msg.answer("Пожалуйста, отправьте текст, фото, видео или другой поддерживаемый контент.")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT link_id, sender_user_id FROM messages WHERE id = ?",
            (orig_msg_id,)
        )
        msg_row = await cur.fetchone()
        if not msg_row:
            await state.clear()
            await msg.answer("⚠️ Сообщение не найдено. Возможно, оно было удалено.")
            return
        
        link_id, orig_sender_user = msg_row
        
        cur = await db.execute(
            "SELECT tg_user_id FROM users WHERE id = ?",
            (orig_sender_user,)
        )
        user_row = await cur.fetchone()
        if not user_row:
            await state.clear()
            await msg.answer("⚠️ Пользователь не найден.")
            return
        
        orig_tg = user_row[0]
        
        await db.execute(
            "INSERT INTO messages(link_id, sender_user_id, text, media_type, media_file_id, reply_to_id) "
            "VALUES (?, NULL, ?, ?, ?, ?)",
            (link_id, text, media_type, file_id, orig_msg_id)
        )
        await db.commit()

    await send_media(
        bot=bot,
        chat_id=orig_tg,
        media_type=media_type,
        file_id=file_id,
        text=text,
        prefix="✉️ Анонимный ответ:\n\n"
    )
    await state.clear()
    await msg.answer("✅ Ваш ответ отправлен анонимно!")


def register_handlers(dp):
    dp.message.register(owner_reply, Form.waiting_for_reply)
