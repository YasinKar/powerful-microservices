from celery_app import celery_app


@celery_app.task(
    queue="notifications_default",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 10},
)
def send_sms_task(to: str, subject: str, body: str):
    pass


@celery_app.task(
    queue="notifications_high",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 10},
)
def send_otp_sms_task(to: str, otp_code: str):
    print("sent OTP")


@celery_app.task(
    queue="notifications_high",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 10},
)
def send_welcome_sms_task(to: str, username: str):
    pass