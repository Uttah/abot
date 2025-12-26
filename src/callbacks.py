from aiogram.filters.callback_data import CallbackData


class ReplyCallback(CallbackData, prefix="reply"):
    message_id: int


class BlockCallback(CallbackData, prefix="block"):
    message_id: int
