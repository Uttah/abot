import aiosqlite

from aiogram import Bot
from aiogram.types import Message

from ..database import DB_PATH
from ..states import Form
from aiogram.fsm.context import FSMContext
from ..keyboards import make_reply_keyboard
from ..media import extract_media, send_media


async def anon_message(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    link_id = data["link_id"]
    tg_sender = msg.from_user.id

    media_type, file_id, text = extract_media(msg)

    if media_type is None and text is None:
        await msg.answer("Пожалуйста, отправьте текст, фото, видео или другой поддерживаемый контент.")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users(tg_user_id) VALUES (?)",
            (tg_sender,)
        )
        await db.commit()
        cur = await db.execute(
            "SELECT id FROM users WHERE tg_user_id = ?",
            (tg_sender,)
        )
        sender_user_id = (await cur.fetchone())[0]
        cur = await db.execute(
            "INSERT INTO messages(link_id, sender_user_id, text, media_type, media_file_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (link_id, sender_user_id, text, media_type, file_id)
        )
        await db.commit()
        message_id = cur.lastrowid
        cur = await db.execute(
            "SELECT u.tg_user_id FROM users u "
            "JOIN links l ON l.owner_id = u.id WHERE l.id = ?",
            (link_id,)
        )
        owner_tg = (await cur.fetchone())[0]

    kb = make_reply_keyboard(message_id)
    await send_media(
        bot=bot,
        chat_id=owner_tg,
        media_type=media_type,
        file_id=file_id,
        text=text,
        reply_markup=kb,
        prefix="📩 Новое анонимное сообщение:\n\n"
    )
    await msg.answer(
        "✅ Ваше сообщение доставлено анонимно.\n"
        "Чтобы задать ещё один вопрос, просто отправьте текст или медиа.\n"
        "Если хотите выйти — введите /stop."
    )


def register_handlers(dp):
    dp.message.register(anon_message, Form.waiting_for_anon)
