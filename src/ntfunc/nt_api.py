from abc import ABCMeta


class NTAPI(metaclass=ABCMeta):
    async def check_account(self, email: str, password: str) -> int:
        ...

    async def change_credentials(self, email: str, password: str, new_password: str) -> None:
        ...
