from projz import ZClient
from projz.internal.exceptions.objects.email_not_registered import EmailNotRegistered
from projz.internal.exceptions.objects.incorrect_password import IncorrectPassword
from projz.internal.exceptions.objects.invalid_email import InvalidEmail
from .nt_api import NTAPI


class Z(ZClient, NTAPI):
    def __init__(self):
        super().__init__(establish_websocket=False)

    async def check_account(self, email: str, password: str) -> int:
        try:
            await self.login(email, password)
            return 0
        except EmailNotRegistered:
            return 1
        except IncorrectPassword:
            return 2
        except InvalidEmail:
            return 3

    async def change_credentials(self, email: str, password: str, new_password: str) -> None:
        await self.change_password(password, new_password)
