import aiosqlite

from aiogram import Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from ..database import DB_PATH
from ..states import Form


async def owner_reply(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    orig_msg_id = data["reply_message_id"]
    text = msg.text

    async with aiosqlite.connect(DB_PATH) as db:
        # get link_id and original sender user ID
        cur = await db.execute(
            "SELECT link_id, sender_user_id FROM messages WHERE id = ?",
            (orig_msg_id,)
        )
        link_id, orig_sender_user = await cur.fetchone()
        # get original sender's Telegram ID
        cur = await db.execute(
            "SELECT tg_user_id FROM users WHERE id = ?",
            (orig_sender_user,)
        )
        orig_tg = (await cur.fetchone())[0]
        # save the reply message
        await db.execute(
            "INSERT INTO messages(link_id, sender_user_id, text, reply_to_id) "
            "VALUES (?, NULL, ?, ?)",
            (link_id, text, orig_msg_id)
        )
        await db.commit()

    await bot.send_message(orig_tg, f"✉️ Анонимный ответ:\n\n{text}")
    await state.clear()
    await msg.answer("✅ Ваш ответ отправлен анонимно!")


def register_handlers(dp):
    dp.message.register(owner_reply, Form.waiting_for_reply)
