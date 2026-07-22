from aiogram.fsm.state import State, StatesGroup

class BroadcastStates(StatesGroup):
    waiting_for_content = State()
    confirm_broadcast = State()

class GroupStates(StatesGroup):
    searching = State()