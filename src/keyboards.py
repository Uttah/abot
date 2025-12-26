from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .callbacks import ReplyCallback, BlockCallback


def make_reply_keyboard(message_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✏️ Ответить",
                callback_data=ReplyCallback(message_id=message_id).pack()
            ),
            InlineKeyboardButton(
                text="🚫 Заблокировать",
                callback_data=BlockCallback(message_id=message_id).pack()
            )
        ]
    ])
