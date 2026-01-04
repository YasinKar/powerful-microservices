from tasks.email_tasks import send_otp_email_task
from tasks.sms_tasks import send_otp_sms_task


def handle_user_registered(payload: dict):
        user_type = payload.get("user_type")
        username = payload.get("username")
        otp = payload.get("otp")

        if user_type == "phone":
            send_otp_sms_task.apply_async(args=[username, otp], routing_key="notifications.high")
        elif user_type == "email":
            send_otp_email_task.apply_async(args=[username, otp], routing_key="notifications.high")