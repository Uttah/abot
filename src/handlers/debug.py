from aiogram.types import Message
from aiogram.fsm.context import FSMContext


async def debug_state(msg: Message, state: FSMContext):
    current = await state.get_state()
    await msg.answer(f"DEBUG state: {current}")


def register_handlers(dp):
    dp.message.register(debug_state)
