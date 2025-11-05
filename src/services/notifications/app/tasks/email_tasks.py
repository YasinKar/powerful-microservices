from celery_app import celery_app
from providers.email_provider import EmailProvider


@celery_app.task(
    queue="notifications_default",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 10},
)
def send_email_task(to: str, subject: str, body: str, html: str | None = None):
    """Celery task to send email asynchronously."""
    provider = EmailProvider()
    provider.send(to, subject, body, html)


@celery_app.task(
    queue="notifications_high",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 10},
)
def send_otp_email_task(to: str, otp_code: str):
    """Send OTP email."""
    subject = "Your OTP Code"
    body = f"Your OTP code is: {otp_code}\nIt will expire in 5 minutes."
    provider = EmailProvider()
    provider.send(to, subject, body)


@celery_app.task(
    queue="notifications_high",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 10},
)
def send_welcome_email_task(username: str):
    """Send welcome email."""
    subject = "Welcome to Our Platform 🎉"
    body = f"Hi {username},\n\nWelcome to our platform! We’re glad to have you."
    provider = EmailProvider()
    provider.send(username, subject, body)
