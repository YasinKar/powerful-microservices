from tasks.email_tasks import send_welcome_email_task
from tasks.sms_tasks import send_welcome_sms_task


def handle_user_verified(payload: dict):
        user_type = payload.get("user_type")
        username = payload.get("username")

        if user_type == "phone":
            send_welcome_sms_task.apply_async(args=[username], routing_key="notifications.default")
        elif user_type == "email":
            send_welcome_email_task.apply_async(args=[username], routing_key="notifications.default")