import aiosqlite

from aiogram import Bot
from aiogram.types import Message

from ..database import DB_PATH
from ..states import Form
from aiogram.fsm.context import FSMContext
from ..keyboards import make_reply_keyboard


async def anon_message(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    link_id = data["link_id"]
    tg_sender = msg.from_user.id
    text = msg.text

    async with aiosqlite.connect(DB_PATH) as db:
        # add sender to users table if not exists
        await db.execute(
            "INSERT OR IGNORE INTO users(tg_user_id) VALUES (?)",
            (tg_sender,)
        )
        await db.commit()
        # get sender user id
        cur = await db.execute(
            "SELECT id FROM users WHERE tg_user_id = ?",
            (tg_sender,)
        )
        sender_user_id = (await cur.fetchone())[0]
        # save the message
        cur = await db.execute(
            "INSERT INTO messages(link_id, sender_user_id, text) VALUES (?, ?, ?)",
            (link_id, sender_user_id, text)
        )
        await db.commit()
        message_id = cur.lastrowid
        # get the owner of the link
        cur = await db.execute(
            "SELECT u.tg_user_id FROM users u "
            "JOIN links l ON l.owner_id = u.id WHERE l.id = ?",
            (link_id,)
        )
        owner_tg = (await cur.fetchone())[0]

    kb = make_reply_keyboard(message_id)
    await bot.send_message(
        owner_tg,
        f"📩 Новое анонимное сообщение:\n\n{text}",
        reply_markup=kb
    )
    await msg.answer(
        "✅ Ваше сообщение доставлено анонимно.\n"
        "Чтобы задать ещё один вопрос, просто введите текст.\n"
        "Если хотите выйти — введите /stop."
    )


def register_handlers(dp):
    dp.message.register(anon_message, Form.waiting_for_anon)
