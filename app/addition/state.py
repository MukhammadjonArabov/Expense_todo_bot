from aiogram.fsm.state import State, StatesGroup

class DeleteExpense(StatesGroup):
    waiting_for_id = State()

class AddExpense(StatesGroup):
    amount = State()
    reason = State()
    date = State()

class AddPersonalTask(StatesGroup):
    title = State()
    month_day = State()
    description = State()