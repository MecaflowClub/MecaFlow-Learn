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
    try:
        print(f"Starting email send process to {email}")
        
        # Validate SMTP settings
        if not SMTP_USER or not SMTP_PASSWORD:
            raise ValueError("SMTP credentials not configured")
            
        # Prepare email
        subject = "Your Verification Code"
        body = f"Your verification code is: {code}"
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = email
        
        print(f"Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT}")
        
        # Set timeout for SMTP operations
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.set_debuglevel(1)  # Enable debug output
            print("Starting TLS")
            server.starttls()
            
            print("Attempting login")
            server.login(SMTP_USER, SMTP_PASSWORD)
            
            print("Sending email")
            server.sendmail(SMTP_USER, [email], msg.as_string())
            print(f"Verification code successfully sent to {email}")
            return True
            
    except smtplib.SMTPAuthenticationError:
        print("SMTP Authentication failed - check username and password")
        raise ValueError("Email authentication failed")
    except smtplib.SMTPException as e:
        print(f"SMTP error occurred: {str(e)}")
        raise ValueError(f"Failed to send email: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise ValueError(f"Failed to send email: {str(e)}")
