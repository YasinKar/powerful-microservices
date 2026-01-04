from dataclasses import dataclass, asdict
from typing import Literal

from .base import BaseEvent


@dataclass
class UserVerifiedPayload:
    user_type: Literal["phone", "email"]
    username: str


class UserVerifiedEvent:
    EVENT_TYPE = "UserVerified"

    @staticmethod
    def create(payload: UserVerifiedPayload) -> BaseEvent:
        return BaseEvent.new(
            event_type=UserVerifiedEvent.EVENT_TYPE,
            data=asdict(payload),
        )