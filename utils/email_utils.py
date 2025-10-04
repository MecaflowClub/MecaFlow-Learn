from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger("cad-platform")

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
                <h2>Bienvenue sur MecaFlow Learn!</h2>
                <p>Votre code de vérification est : <strong>{code}</strong></p>
                <p>Ce code expirera dans 10 minutes.</p>
                <br>
                <p>Cordialement,<br>L'équipe MecaFlow</p>
                """
            )
        )

        # Send via SendGrid API
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        logger.info(f"Sending verification email to: {email}")
        response = sg.send(message)
        
        if response.status_code == 403:
            logger.error("SendGrid authentication failed (403 Forbidden)")
            logger.error("Please check:")
            logger.error("1. API key has 'Mail Send' permission")
            logger.error("2. Sender email is verified")
            logger.error("3. API key is valid and not revoked")
            raise ValueError("SendGrid authentication failed - check API key permissions")
            
        if response.status_code not in [200, 202]:
            logger.error(f"SendGrid API error: Status {response.status_code}")
            logger.error(f"Response headers: {response.headers}")
            raise ValueError(f"SendGrid API error: {response.status_code}")
            
        logger.info(f"Verification email sent successfully to {email}")
        return True

    except SendGridAPIClient.AuthenticationError as e:
        logger.error(f"SendGrid authentication failed: {str(e)}")
        raise ValueError("Authentication failed - please check your SendGrid API key")
    except SendGridAPIClient.APIError as e:
        logger.error(f"SendGrid API error: {str(e)}")
        logger.error(f"Response status: {getattr(e, 'status_code', 'N/A')}")
        logger.error(f"Response body: {getattr(e, 'body', 'N/A')}")
        raise ValueError(f"SendGrid API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error sending verification email: {str(e)}")
        logger.exception("Full error traceback:")
        raise ValueError(f"Failed to send email: {str(e)}")