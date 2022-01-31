from httpx import AsyncClient
from hmac import new
from hashlib import sha1
from os import urandom
from base64 import b64encode
from ujson import dumps
from ujson import loads
from time import time
from typing import Optional
from uuid import uuid4
from .nt_api import NTAPI


class Amino(NTAPI):
    def __init__(self) -> None:
        self.api_url = "http://service.narvii.com/api/v1"
        self.headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 7.1.2; SM-G977N Build/beyond1qlteue-user 7; com.narvii.amino.master/3.4.33597)",
            "Connection": "Keep-Alive",
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json"
        }
        self.sid = None

    def _signature(self, data: str) -> str:
        mac = new(bytes.fromhex("fbf98eb3a07a9042ee5593b10ce9f3286a69d4e2"), data.encode("utf-8"), sha1)
        return b64encode(bytes.fromhex("32") + mac.digest()).decode("utf-8")

    def _device_id(self) -> str:
        rand = urandom(30)
        mac = new(bytes.fromhex("76b4a156aaccade137b8b1e77b435a81971fbd3e"), "2".encode() + rand, sha1)
        device = "32" + rand.hex() + mac.hexdigest()
        return device.upper()

    async def get_sid(self, email: str, password: str) -> str:
        headers = self.headers.copy()
        data = dumps({
            "email": email,
            "v": 2,
            "secret": f"0 " + password,
            "deviceID": self._device_id(),
            "clientType": 100,
            "action": "normal",
            "timestamp": int(time() * 1000)
        })
        headers["NDCDEVICEID"] = self._device_id()
        headers["NDC-MSG-SIG"] = self._signature(data)
        async with AsyncClient(base_url=self.api_url) as client:
            response = await client.post("/g/s/auth/login", headers=headers, data=data)
            body = loads(response.text)
        return "sid=" + body["sid"]

    async def join(self, ndc_id: str, sid: str) -> bool:
        headers = self.headers.copy()
        data = dumps({
            "timestamp": (time() * 1000)
        })
        headers["NDCDEVICEID"] = self._device_id()
        headers["NDC-MSG-SIG"] = self._signature(data)
        headers["NDCAUTH"] = sid
        async with AsyncClient(base_url=self.api_url) as client:
            response = await client.post(self.api_url + f"/{ndc_id}/s/community/join", headers=headers, data=data)
            json = await response.json()
            if json["api:statuscode"] != 0:
                message = json["api:message"]
                print(f"Joining request error: {message}")
                return False
            return True

    async def leave(self, ndc_id: str, sid: str) -> bool:
        headers = self.headers.copy()
        data = dumps({
            "timestamp": (time() * 1000)
        })
        headers["NDCDEVICEID"] = self._device_id()
        headers["NDC-MSG-SIG"] = self._signature(data)
        headers["NDCAUTH"] = sid
        async with AsyncClient(base_url=self.api_url) as client:
            response = await client.post(self.api_url + f"/{ndc_id}/s/community/leave", headers=headers, data=data)
            json = await response.json()
            if json["api:statuscode"] != 0:
                message = json["api:message"]
                print(f"Leaving request error: {message}")
                return False
            return True

    async def post_ids(self, post_link: str) -> Optional[tuple]:
        headers = self.headers.copy()
        headers["NDCDEVICEID"] = self._device_id()
        async with AsyncClient(base_url=self.api_url) as client:
            response = await client.get(
                f"https://service.narvii.com/api/v1/g/s/link-resolution?q={post_link}",
                headers=headers
            )
            resolution = await response.json()
            try:
                return resolution["linkInfoV2"]["extensions"]["linkInfo"]["objectId"], \
                        resolution["linkInfoV2"]["path"].split("/")[0]
            except KeyError:
                return None

    async def check_account(self, email: str, password: str) -> int:
        headers = self.headers.copy()
        data = dumps({
            "email": email,
            "v": 2,
            "secret": f"0 " + password,
            "deviceID": self._device_id(),
            "clientType": 100,
            "action": "normal",
            "timestamp": int(time() * 1000)
        })
        headers["NDCDEVICEID"] = self._device_id()
        headers["NDC-MSG-SIG"] = self._signature(data)
        async with AsyncClient(base_url=self.api_url) as client:
            response = await client.post("/g/s/auth/login", headers=headers, data=data)
            body = loads(response.text)
            code = body["api:statuscode"]
            if code == 200:
                return 1
            elif code == 216:
                return 2
            elif code == 213:
                return 3
            self.sid = "sid=" + body["sid"]
            return 0

    async def change_credentials(self, email: str, password: str, new_password: str) -> None:
        headers = self.headers.copy()
        data = dumps({
            "secret": "0 " + password,
            "updateSecret": "0 " + new_password,
            "validationContext": None,
            "deviceID": self._device_id()
        })
        headers["NDCDEVICEID"] = self._device_id()
        headers["NDC-MSG-SIG"] = self._signature(data)
        headers["NDCAUTH"] = self.sid
        async with AsyncClient(base_url=self.api_url) as client:
            response = await client.post("/g/s/auth/change-password", headers=headers, data=data)
            body = loads(response.text)
            if body["api:statuscode"] != 0:
                print(f"Ошибка при смене пароля: {body['api:message']}")
                raise Exception()

    @classmethod
    async def send_coins(cls, link: str, count: int) -> int:
        instance = cls()
        headers = instance.headers.copy()
        headers["NDCDEVICEID"] = instance._device_id()
        headers["NDCAUTH"] = await instance.get_sid("почта от аккаунта с монетами", "пароль от аккаунта с монетами")
        ids = await instance.post_ids(link)
        if ids is None:
            return 1
        blog_id, ndc_id = ids
        join_result = await instance.join(ndc_id, headers["NDCAUTH"])
        if not join_result:
            return 2
        data = dumps({
            "coins": count,
            "tippingContext": {"transactionId": str(uuid4())},
            "timestamp": int(time() * 1000)
        })
        headers["NDC-MSG-SIG"] = instance._signature(data)
        async with AsyncClient(base_url=instance.api_url) as client:
            response = await client.post(f"/{ndc_id}/s/blog/{blog_id}/tipping", headers=headers, data=data)
            body = loads(response.text)
            code = body["api:statuscode"]
            if code == 0:
                await instance.leave(ndc_id, headers["NDCAUTH"])
                return 0
            return 3

