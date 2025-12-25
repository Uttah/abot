import aiosqlite

from aiogram import Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from ..database import DB_PATH
from ..states import Form
from ..media import extract_media, send_media


async def owner_reply(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    orig_msg_id = data["reply_message_id"]

    media_type, file_id, text = extract_media(msg)

    if media_type is None and text is None:
        await msg.answer("Пожалуйста, отправьте текст, фото, видео или другой поддерживаемый контент.")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT link_id, sender_user_id FROM messages WHERE id = ?",
            (orig_msg_id,)
        )
        link_id, orig_sender_user = await cur.fetchone()
        cur = await db.execute(
            "SELECT tg_user_id FROM users WHERE id = ?",
            (orig_sender_user,)
        )
        orig_tg = (await cur.fetchone())[0]
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
