from events.schemas.base import BaseEvent
from events.schemas.user_registered import UserRegisteredEvent, UserRegisteredPayload
from events.schemas.user_verified import UserVerifiedEvent, UserVerifiedPayload


def test_base_event_new_builds_required_fields():
    event = BaseEvent.new(event_type="Sample", data={"k": "v"})

    assert event.event_type == "Sample"
    assert event.version == 1
    assert event.data == {"k": "v"}
    assert event.event_id
    assert event.occurred_at


def test_user_registered_event_factory():
    payload = UserRegisteredPayload(user_type="email", username="a@b.com", otp=123456)
    event = UserRegisteredEvent.create(payload)

    assert event.event_type == "UserRegistered"
    assert event.data["username"] == "a@b.com"
    assert event.data["otp"] == 123456


def test_user_verified_event_factory():
    payload = UserVerifiedPayload(user_type="phone", username="+15551234567")
    event = UserVerifiedEvent.create(payload)

    assert event.event_type == "UserVerified"
    assert event.data == {"user_type": "phone", "username": "+15551234567"}
