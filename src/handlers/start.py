import secrets
import aiosqlite

from aiogram import F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from ..database import DB_PATH
from ..states import Form
from ..config import ADMIN_IDS


async def cmd_start(msg: Message, state: FSMContext, bot: Bot):
    await state.clear()
    
    if not msg.text or not msg.from_user:
        return
    
    parts = msg.text.split(maxsplit=1)

    # check the code
    if len(parts) > 1:
        code = parts[1]
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                "SELECT id FROM links WHERE code = ?",
                (code,)
            )
            row = await cur.fetchone()
        if not row:
            return await msg.answer("❌ Неверный или устаревший код.")
        link_id = row[0]
        await state.update_data(link_id=link_id)
        await state.set_state(Form.waiting_for_anon)
        return await msg.answer("✏️ Введите текст вашего анонимного сообщения:")

    # else create a new link (only for admins)
    tg = msg.from_user.id
    
    if tg not in ADMIN_IDS:
        await msg.answer("👋 Этот бот предназначен для отправки анонимных сообщений.\n\nПерейдите по ссылке от владельца, чтобы отправить сообщение.")
        return
    
    async with aiosqlite.connect(DB_PATH) as db:
        # register user if not exists
        await db.execute(
            "INSERT OR IGNORE INTO users(tg_user_id) VALUES (?)",
            (tg,)
        )
        await db.commit()
        cur = await db.execute(
            "SELECT id FROM users WHERE tg_user_id = ?",
            (tg,)
        )
        user_row = await cur.fetchone()
        if not user_row:
            await msg.answer("⚠️ Ошибка при создании пользователя. Попробуйте ещё раз.")
            return
        user_id = user_row[0]

        # create code and insert into links
        code = secrets.token_urlsafe(8)
        await db.execute(
            "INSERT INTO links(code, owner_id) VALUES (?, ?)",
            (code, user_id)
        )
        await db.commit()

    bot_username = (await bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={code}"
    await msg.answer(
        "✨ Ваша уникальная ссылка для приёма анонимных сообщений:\n\n"
        f"{link}\n\n"
        "Скопируйте этот код и введите в этом чате:\n"
        f"<code>/start {code}</code>\n"
        "А затем отправьте текст вопроса.",
        parse_mode="HTML"
    )


def register_handlers(dp):
    dp.message.register(cmd_start, F.text.startswith("/start"))
