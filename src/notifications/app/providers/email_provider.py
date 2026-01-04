import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import settings


logger = logging.getLogger(__name__)


class EmailProvider:
    def __init__(self):
        self.smtp_server = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_USE_TLS
        self.from_name = settings.SMTP_FROM_NAME

    def send(self, to: str, subject: str, body: str, html: str | None = None):
        """
        Send an email with plain text or HTML content.
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.username}>"
            msg["To"] = to

            # Plain text
            part1 = MIMEText(body, "plain")
            msg.attach(part1)

            # HTML part (optional)
            if html:
                part2 = MIMEText(html, "html")
                msg.attach(part2)

            with smtplib.SMTP(self.smtp_server, self.port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"Email sent to {to}")

        except smtplib.SMTPException as e:
            logger.error(f"Failed to send email to {to}: {e}")
            raise
