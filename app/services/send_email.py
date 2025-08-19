import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import Optional

from app.services.config import CONFIG, get_recipient_emails
from app.services.utils import retry_email

@retry_email()
def send_email(
    subject: str = "Person Unit Info CSV",
    html_content: str = "Attached is your CSV data.",
    csv_content: Optional[str] = None,
):
    """
    Send an email with optional CSV attachment via SMTP.
    """
    if not CONFIG.smtp_username or not CONFIG.smtp_password:
        raise ValueError("SMTP credentials not set in environment variables")

    recipients = get_recipient_emails()

    msg = EmailMessage()
    msg["From"] = CONFIG.smtp_username
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(html_content, subtype="html")

    if csv_content:
        today_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"ActionBuilder_Sync_Export_{today_str}.csv"
        msg.add_attachment(
            csv_content.encode(),
            maintype="text",
            subtype="csv",
            filename=filename,
        )

    # Send the email
    with smtplib.SMTP(CONFIG.smtp_server, CONFIG.smtp_port) as server:
        server.starttls()
        server.login(CONFIG.smtp_username, CONFIG.smtp_password)
        server.send_message(msg)

    print("Email sent successfully!")


if __name__ == "__main__":
    send_email()
