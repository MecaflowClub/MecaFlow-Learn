from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import os
from dotenv import load_dotenv

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "mecaflowlearn@gmail.com")
FROM_NAME = os.getenv("FROM_NAME", "MecaFlow")

def send_verification_code(email: str, code: str):
    if not SENDGRID_API_KEY:
        raise ValueError("SendGrid API key not configured")

    try:
        # Create message
        message = Mail(
            from_email=Email(FROM_EMAIL, FROM_NAME),
            to_emails=To(email),
            subject="MecaFlow - Code de vérification",
            html_content=Content(
                "text/html",
                f"""
                <h2>Bienvenue sur MecaFlow !</h2>
                <p>Votre code de vérification est : <strong>{code}</strong></p>
                <p>Ce code expirera dans 10 minutes.</p>
                <br>
                <p>Cordialement,<br>L'équipe MecaFlow</p>
                """
            )
        )

        # Send via SendGrid API
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        if response.status_code not in [200, 202]:
            raise ValueError(f"SendGrid API error: {response.status_code}")
            
        print(f"Email sent successfully. Status code: {response.status_code}")
        return True

    except Exception as e:
        error_msg = str(e)
        if "does not have permission" in error_msg:
            print("API Key permission error. Please check SendGrid API key permissions.")
        print(f"Error sending email: {error_msg}")
        raise ValueError(f"Failed to send email: {error_msg}")