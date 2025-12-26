from aiogram import Bot
from aiogram.types import CallbackQuery, Message

from ..callbacks import ReplyCallback
from aiogram.fsm.context import FSMContext


async def on_reply_click(
    cb: CallbackQuery,
    callback_data: ReplyCallback,
    state: FSMContext
):
    await state.clear()
    await state.update_data(reply_message_id=callback_data.message_id)
    await state.set_state("Form:waiting_for_reply")
    
    if cb.message and isinstance(cb.message, Message):
        await cb.message.answer("✏️ Введите ваш анонимный ответ:")
    
    await cb.answer()


def register_handlers(dp):
    dp.callback_query.register(on_reply_click, ReplyCallback.filter())
