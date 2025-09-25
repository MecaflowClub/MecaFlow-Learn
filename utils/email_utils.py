import smtplib
from email.mime.text import MIMEText
import os
import time
import asyncio
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

FROM_EMAIL = os.getenv("FROM_EMAIL", "mecaflowlearn@gmail.com")
FROM_NAME = os.getenv("FROM_NAME", "MecaFlow")


# Usage: send_verification_code(email, code)
def send_verification_code(email: str, code: str):
    try:
        print(f"Starting email send process to {email}")
        print(f"Using SMTP settings: Server={SMTP_SERVER}, Port={SMTP_PORT}, User={SMTP_USER}")
        
        # Validate SMTP settings
        if not SMTP_USER or not SMTP_PASSWORD:
            print("ERROR: SMTP credentials missing")
            raise ValueError("SMTP credentials not configured")
            
        # Prepare email
        subject = "Your Verification Code"
        body = f"""
        Welcome to MecaFlow!
        
        Your verification code is: {code}
        
        This code will expire in 10 minutes.
        
        Best regards,
        The MecaFlow Team
        """
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg["To"] = email
        
        print(f"Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT}")
        
        # Set timeout for SMTP operations and increase retries
        for attempt in range(3):  # Try 3 times
            try:
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
                    server.set_debuglevel(2)  # Increase debug level
                    print("Starting TLS")
                    server.starttls()
                    
                    print(f"Attempting login with user: {SMTP_USER}")
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    
                    print("Sending email...")
                    result = server.sendmail(FROM_EMAIL, [email], msg.as_string())
                    if result:
                        print(f"Send result: {result}")
                    print(f"✓ Verification code successfully sent to {email}")
                    return True
            except (smtplib.SMTPConnectError, OSError) as e:
                print(f"Connection error on attempt {attempt + 1}: {str(e)}")
                if attempt < 2:
                    print(f"Retrying in 2 seconds... ({attempt + 1}/3)")
                    time.sleep(2)
                else:
                    print("All connection attempts failed")
                    raise
            
    except smtplib.SMTPAuthenticationError as auth_error:
        error_msg = f"SMTP Authentication failed: {str(auth_error)}"
        print(error_msg)
        raise ValueError(error_msg)
    except smtplib.SMTPException as smtp_error:
        error_msg = f"SMTP error occurred: {str(smtp_error)}"
        print(error_msg)
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        raise ValueError(error_msg)

    return False
