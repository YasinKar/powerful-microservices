import pytest
from django.contrib.auth import get_user_model

from api.models import Outbox, ProfileModel


@pytest.mark.django_db
def test_user_manager_create_user_hashes_password():
    user = get_user_model().objects.create_user(
        username="new@example.com",
        password="Aa123456!",
    )

    assert user.username == "new@example.com"
    assert user.check_password("Aa123456!")
    assert user.is_admin is False


@pytest.mark.django_db
def test_user_manager_create_user_without_username_raises():
    with pytest.raises(ValueError, match="please insert username"):
        get_user_model().objects.create_user(username="", password="Aa123456!")


@pytest.mark.django_db
def test_user_manager_create_superuser_sets_admin_flag():
    user = get_user_model().objects.create_superuser(
        username="admin@example.com",
        password="Aa123456!",
    )

    assert user.is_admin is True


@pytest.mark.django_db
def test_profile_model_string_representation(user):
    profile = ProfileModel.objects.create(
        user=user,
        first_name="Jane",
        last_name="Doe",
    )

    assert str(profile) == f"{user.username} - ({profile.pk})"


@pytest.mark.django_db
def test_outbox_defaults_and_string_representation():
    outbox = Outbox.objects.create(
        topic="users",
        value='{"hello":"world"}',
    )

    assert outbox.status == "pending"
    assert outbox.retry_count == 0
    assert str(outbox) == "users - pending"
