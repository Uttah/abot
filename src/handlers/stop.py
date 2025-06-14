from aiogram.types import Message
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext


async def cmd_stop(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "✅ Сессия анонимных сообщений завершена.\n"
        "Чтобы задать новый вопрос, введите:\n"
        "<code>/start <CODE></code>",
        parse_mode="HTML"
    )


def register_handlers(dp):
    dp.message.register(cmd_stop, Command(commands=["stop"]))
