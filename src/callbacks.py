from aiogram.filters.callback_data import CallbackData


class ReplyCallback(CallbackData, prefix="reply"):
    message_id: int
