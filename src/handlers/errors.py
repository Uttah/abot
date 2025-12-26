import logging
from aiogram import Router
from aiogram.types import ErrorEvent
from aiogram.filters import ExceptionTypeFilter

logger = logging.getLogger(__name__)

router = Router()


@router.error(ExceptionTypeFilter(KeyError))
async def handle_state_error(event: ErrorEvent):
    """Обработка ошибок когда FSM state потерян (например после перезапуска)."""
    update = event.update
    user_id = "unknown"
    if update.message and update.message.from_user:
        user_id = update.message.from_user.id
    elif update.callback_query and update.callback_query.from_user:
        user_id = update.callback_query.from_user.id
    
    logger.warning("State data missing for user %s: %s", user_id, event.exception)
    
    if update.message:
        await update.message.answer(
            "⚠️ Сессия истекла. Пожалуйста, начните заново с /start"
        )
    elif update.callback_query:
        await update.callback_query.answer(
            "⚠️ Сессия истекла. Начните заново с /start",
            show_alert=True
        )
    
    return True  # Ошибка обработана


@router.error(ExceptionTypeFilter(TypeError))
async def handle_none_error(event: ErrorEvent):
    """Обработка ошибок когда данные не найдены в БД."""
    update = event.update
    user_id = "unknown"
    if update.message and update.message.from_user:
        user_id = update.message.from_user.id
    elif update.callback_query and update.callback_query.from_user:
        user_id = update.callback_query.from_user.id
    
    logger.warning("Database returned None for user %s: %s", user_id, event.exception)
    
    if update.message:
        await update.message.answer(
            "⚠️ Данные не найдены. Попробуйте начать заново с /start"
        )
    elif update.callback_query:
        await update.callback_query.answer(
            "⚠️ Данные не найдены. Начните заново с /start",
            show_alert=True
        )
    
    return True


@router.error()
async def handle_unexpected_error(event: ErrorEvent):
    """Глобальный обработчик всех остальных ошибок."""
    update = event.update
    
    logger.exception(
        "Unhandled exception for update %s: %s",
        update.update_id,
        event.exception
    )
    
    try:
        if update.message:
            await update.message.answer(
                "❌ Произошла непредвиденная ошибка. Попробуйте позже или начните заново с /start"
            )
        elif update.callback_query:
            await update.callback_query.answer(
                "❌ Произошла ошибка. Попробуйте позже.",
                show_alert=True
            )
    except Exception as e:
        logger.error("Failed to send error message to user: %s", e)
    
    return True
