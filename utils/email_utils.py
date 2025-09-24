import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


# Usage: send_verification_code(email, code)
def send_verification_code(email: str, code: str):
    subject = "Your Verification Code"
    body = f"Your verification code is: {code}"
    msg = MIMEText(body)
    msg["Subject"] = subject
    if not SMTP_USER:
        raise ValueError("SMTP_USER is not set")
    msg["From"] = SMTP_USER
    msg["To"] = email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        if not SMTP_USER or not SMTP_PASSWORD:
            raise ValueError("SMTP_USER or SMTP_PASSWORD is not set")
        server.login(SMTP_USER, SMTP_PASSWORD)
        if not SMTP_USER:
            raise ValueError("SMTP_USER is not set")
        server.sendmail(SMTP_USER, [email], msg.as_string())
        print(f"Verification code sent to {email}")
