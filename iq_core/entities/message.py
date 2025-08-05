from dataclasses import dataclass
from typing import Any, Literal, ClassVar, Self
from enum import Enum
from time import monotonic, time
from random import randint
import json


class MessageType(str, Enum):
    SEND = "sendMessage"
    SUBSCRIBE = "subscribeMessage"
    UNSUBSCRIBE = "unsubscribeMessage"
    SET_OPTIONS = "setOptions"
    AUTHENTICATE = "authenticate"


@dataclass(frozen=True, slots=True, kw_only=True)
class Message:
    """
    WebSocket message representation for IQ Option.

    Representação de mensagem WebSocket para a IQ Option.
    """

    name: str
    request_id: str
    local_time: int
    msg: dict[str, Any]

    _start_monotonic: ClassVar[float] = monotonic()

    @classmethod
    def _local_time(cls) -> int:
        """Tempo relativo à conexão em milissegundos"""
        return int((monotonic() - cls._start_monotonic) * 1000)

    @classmethod
    def send(cls, request_id: int, msg: dict[str, Any]) -> Self:
        return cls(
            name=MessageType.SEND,
            request_id=str(request_id),
            local_time=cls._local_time(),
            msg=msg,
        )

    @classmethod
    def subscribe(
        cls,
        sid: int,
        name: str,
        version: Literal["1.0", "2.0", "3.0", "4.0", "5.0"] | None,
        params: dict | None = None,
    ) -> Self:
        params = params or {}
        message = {"name": name, "params": params}

        if version is not None:
            message["version"] = version

        return cls(
            name=MessageType.SUBSCRIBE,
            request_id=f"s_{sid}",
            local_time=cls._local_time(),
            msg=message,
        )

    @classmethod
    def unsubscribe(
        cls,
        sid: int,
        name: str,
        version: Literal["1.0", "2.0", "3.0", "4.0", "5.0"] | None,
        params: dict | None = None,
    ) -> Self:
        params = params or {}
        message = {"name": name, "params": params}

        if version is not None:
            message["version"] = version

        return cls(
            name=MessageType.UNSUBSCRIBE,
            request_id=f"s_{sid}",
            local_time=cls._local_time(),
            msg=message,
        )

    @classmethod
    def set_options(cls, request_id: int, send_results: bool = True) -> Self:
        return cls(
            name=MessageType.SET_OPTIONS,
            request_id=str(request_id),
            local_time=cls._local_time(),
            msg={"sendResults": send_results},
        )

    @classmethod
    def authenticate(cls, ssid: str) -> Self:
        return cls(
            name=MessageType.AUTHENTICATE,
            request_id=f"{int(time())}_{randint(1_000_000_000, 9_999_999_999)}",
            local_time=cls._local_time(),
            msg={
                "ssid": ssid,
                "protocol": 3,
                "session_id": "",
                "client_session_id": "",
            },
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        if not {"name", "request_id", "local_time", "msg"} <= data.keys():
            raise ValueError("Missing required fields in message dictionary.")
        return cls(
            name=data["name"],
            request_id=data["request_id"],
            local_time=data["local_time"],
            msg=data["msg"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "request_id": self.request_id,
            "local_time": self.local_time,
            "msg": self.msg,
        }

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def __repr__(self) -> str:
        return f"<Message name={self.name!r} id={self.request_id!r} time={self.local_time}>"
