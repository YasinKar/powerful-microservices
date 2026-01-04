from dataclasses import dataclass, asdict
from typing import Literal

from .base import BaseEvent


@dataclass
class UserRegisteredPayload:
    user_type: Literal["phone", "email"]
    username: str
    otp: int


class UserRegisteredEvent:
    EVENT_TYPE = "UserRegistered"

    @staticmethod
    def create(payload: UserRegisteredPayload) -> BaseEvent:
        return BaseEvent.new(
            event_type=UserRegisteredEvent.EVENT_TYPE,
            data=asdict(payload),
        )