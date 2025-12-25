from aiogram import Bot
from aiogram.types import Message


MEDIA_TYPES = ("photo", "video", "animation", "voice", "video_note", "sticker", "document", "audio")


def extract_media(msg: Message) -> tuple[str | None, str | None, str | None]:
    """
    Извлекает информацию о медиа из сообщения.
    
    Returns:
        (media_type, file_id, caption/text)
    """
    if msg.photo:
        return "photo", msg.photo[-1].file_id, msg.caption
    elif msg.video:
        return "video", msg.video.file_id, msg.caption
    elif msg.animation:
        return "animation", msg.animation.file_id, msg.caption
    elif msg.voice:
        return "voice", msg.voice.file_id, msg.caption
    elif msg.video_note:
        return "video_note", msg.video_note.file_id, None
    elif msg.sticker:
        return "sticker", msg.sticker.file_id, None
    elif msg.document:
        return "document", msg.document.file_id, msg.caption
    elif msg.audio:
        return "audio", msg.audio.file_id, msg.caption
    elif msg.text:
        return None, None, msg.text
    else:
        return None, None, None


async def send_media(
    bot: Bot,
    chat_id: int,
    media_type: str | None,
    file_id: str | None,
    text: str | None,
    reply_markup=None,
    prefix: str = ""
) -> Message:
    """
    Отправляет сообщение с медиа или текст.
    """
    caption = f"{prefix}{text}" if text else (prefix.rstrip("\n") if prefix else None)
    
    if media_type is None:
        return await bot.send_message(chat_id, caption or prefix, reply_markup=reply_markup)
    
    elif media_type == "photo":
        return await bot.send_photo(chat_id, file_id, caption=caption, reply_markup=reply_markup)
    
    elif media_type == "video":
        return await bot.send_video(chat_id, file_id, caption=caption, reply_markup=reply_markup)
    
    elif media_type == "animation":
        return await bot.send_animation(chat_id, file_id, caption=caption, reply_markup=reply_markup)
    
    elif media_type == "voice":
        return await bot.send_voice(chat_id, file_id, caption=caption, reply_markup=reply_markup)
    
    elif media_type == "video_note":
        sent = await bot.send_video_note(chat_id, file_id)
        if prefix:
            await bot.send_message(chat_id, prefix.rstrip("\n"), reply_markup=reply_markup)
        return sent
    
    elif media_type == "sticker":
        sent = await bot.send_sticker(chat_id, file_id)
        if prefix:
            await bot.send_message(chat_id, prefix.rstrip("\n"), reply_markup=reply_markup)
        return sent
    
    elif media_type == "document":
        return await bot.send_document(chat_id, file_id, caption=caption, reply_markup=reply_markup)
    
    elif media_type == "audio":
        return await bot.send_audio(chat_id, file_id, caption=caption, reply_markup=reply_markup)
    
    else:
        return await bot.send_message(chat_id, caption or "[Неподдерживаемый контент]", reply_markup=reply_markup)
