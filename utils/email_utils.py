import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from dotenv import load_dotenv

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")  # Utilise la même variable que précédemment
FROM_EMAIL = os.getenv("FROM_EMAIL", "mecaflowlearn@gmail.com")
FROM_NAME = os.getenv("FROM_NAME", "MecaFlow")

def send_verification_code(email: str, code: str):
    if not SENDGRID_API_KEY:
        raise ValueError("SendGrid API key not configured")

    try:
        # Création du message
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

        # Envoi via l'API SendGrid
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        print(f"Email envoyé avec succès. Status code: {response.status_code}")
        return True

    except Exception as e:
        error_msg = str(e)
        print(f"Erreur lors de l'envoi de l'email: {error_msg}")
        if "401" in error_msg:
            raise ValueError("Invalid API Key configuration")
        elif "403" in error_msg:
            raise ValueError("SendGrid API Key does not have permission to send emails")
        elif "from address" in error_msg.lower():
            raise ValueError("Sender email address not verified in SendGrid")
        else:
            raise ValueError(f"Failed to send email: {error_msg}")