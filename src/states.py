from aiogram.dispatcher.filters.state import State
from aiogram.dispatcher.filters.state import StatesGroup


class States(StatesGroup):
    waiting_for_amino_email = State()
    waiting_for_project_z_email = State()
    waiting_for_amino_password = State()
    waiting_for_project_z_password = State()
    waiting_for_post_link = State()
