from aiogram.fsm.state import StatesGroup, State


class Form(StatesGroup):
    waiting_for_anon = State()
    waiting_for_reply = State()
