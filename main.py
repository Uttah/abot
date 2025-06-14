import asyncio
import logging
import os
import secrets

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart, StateFilter, CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State

import aiosqlite

API_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)


class Form(StatesGroup):
    waiting_for_anon = State()    # ждем анонимного сообщения
    waiting_for_reply = State()   # ждем ответа владельца на конкретное сообщение

# Callback-data для кнопки «Ответить»


class ReplyCallback(CallbackData, prefix="reply"):
    message_id: int


async def init_db():
    async with aiosqlite.connect("anonbot.db") as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        # Таблица пользователей-владельцев
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_user_id INTEGER UNIQUE NOT NULL
        );
        """)
        # Таблица ссылок
        await db.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            code     TEXT UNIQUE NOT NULL,
            owner_id INTEGER NOT NULL
              REFERENCES users(id) ON DELETE CASCADE
        );
        """)
        # Таблица сообщений
        await db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id       INTEGER NOT NULL
              REFERENCES links(id) ON DELETE CASCADE,
            sender_tg_id  INTEGER,
            text          TEXT NOT NULL,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            reply_to_id   INTEGER
        );
        """)
        await db.commit()


async def main():
    # инициализируем БД
    await init_db()

    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # === Хэндлер /start ===
    @dp.message(CommandStart())
    async def cmd_start(msg: Message, state: FSMContext, command: CommandStart):
        await state.clear()
        if command.args:
            # Анонимный отправитель пришёл по ссылке /start <code>
            code = command.args
            # ищем link_id
            async with aiosqlite.connect("anonbot.db") as db:
                cur = await db.execute("SELECT id FROM links WHERE code = ?", (code,))
                row = await cur.fetchone()
            if not row:
                await msg.reply("Неверная ссылка.")
                return
            link_id = row[0]
            # запомним link_id в состоянии
            await state.update_data(link_id=link_id)
            await state.set_state(Form.waiting_for_anon)
            await msg.reply("Напишите ваше анонимное сообщение:")
        else:
            # Генерация ссылки для владельца
            tg_id = msg.from_user.id
            async with aiosqlite.connect("anonbot.db") as db:
                # добавляем пользователя, если нет
                await db.execute("INSERT OR IGNORE INTO users(tg_user_id) VALUES(?)", (tg_id,))
                await db.commit()
                # получаем его internal id
                cur = await db.execute("SELECT id FROM users WHERE tg_user_id = ?", (tg_id,))
                user_id = (await cur.fetchone())[0]
                # генерируем уникальный код
                code = secrets.token_urlsafe(8)
                await db.execute("INSERT INTO links(code, owner_id) VALUES(?, ?)", (code, user_id))
                await db.commit()
            link = f"https://t.me/{(await bot.get_me()).username}?start={code}"
            await msg.reply(f"Ваша уникальная ссылка для анонимных сообщений:\n\n{link}")

    # === Приём анонимного сообщения ===
    @dp.message(StateFilter(Form.waiting_for_anon))
    async def anon_message(msg: Message, state: FSMContext):
        data = await state.get_data()
        link_id = data["link_id"]
        sender_id = msg.from_user.id
        text = msg.text

        # сохраняем в БД
        async with aiosqlite.connect("anonbot.db") as db:
            cur = await db.execute(
                "INSERT INTO messages(link_id, sender_tg_id, text) VALUES(?, ?, ?)",
                (link_id, sender_id, text)
            )
            await db.commit()
            message_id = cur.lastrowid

            # получаем owner'а
            cur = await db.execute(
                """SELECT u.tg_user_id
                   FROM users u
                   JOIN links l ON l.owner_id = u.id
                   WHERE l.id = ?""",
                (link_id,)
            )
            owner_tg = (await cur.fetchone())[0]

        # шлём владельцу уведомление с кнопкой «Ответить»
        kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton(
                text="Ответить",
                callback_data=ReplyCallback(message_id=message_id).pack()
            )
        )
        await bot.send_message(owner_tg,
                               f"Новое анонимное сообщение:\n\n{text}",
                               reply_markup=kb)

        await state.clear()
        await msg.reply("Ваше сообщение отправлено анонимно. Спасибо!")

    # === Нажатие кнопки «Ответить» владельцем ===
    @dp.callback_query(ReplyCallback.filter())
    async def on_reply_click(cb: CallbackQuery, callback_data: ReplyCallback, state: FSMContext):
        await state.clear()
        message_id = callback_data.message_id
        # запомним в состоянии, что владелец отвечает на это сообщение
        await state.update_data(reply_message_id=message_id)
        await state.set_state(Form.waiting_for_reply)
        await cb.message.answer("Введите ваш анонимный ответ:")
        await cb.answer()

    # === Приём ответа от владельца ===
    @dp.message(StateFilter(Form.waiting_for_reply))
    async def owner_reply(msg: Message, state: FSMContext):
        data = await state.get_data()
        message_id = data["reply_message_id"]
        text = msg.text

        # сохраняем в БД (связываем reply_to_id)
        async with aiosqlite.connect("anonbot.db") as db:
            # находим link_id и sender_tg_id оригинала
            cur = await db.execute(
                "SELECT link_id, sender_tg_id FROM messages WHERE id = ?",
                (message_id,)
            )
            row = await cur.fetchone()
            link_id, orig_sender = row

            # создаём «ответ» как новую запись, но с reply_to_id
            await db.execute(
                "INSERT INTO messages(link_id, sender_tg_id, text, reply_to_id) VALUES(?, ?, ?, ?)",
                (link_id, None, text, message_id)
            )
            await db.commit()

        # отправляем ответ оригинальному отправителю
        await bot.send_message(orig_sender,
                               f"Анонимный ответ:\n\n{text}")

        await state.clear()
        await msg.reply("Ваш ответ отправлен анонимно.")

    # === Запуск===
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
