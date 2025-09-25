import smtplib
from email.mime.text import MIMEText
import os
import socket
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.sendgrid.net")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", "mecaflowlearn@gmail.com")
FROM_NAME = os.getenv("FROM_NAME", "MecaFlow")

# Timeout configuration
SMTP_TIMEOUT = 10  # seconds

def send_verification_code(email: str, code: str):
    if not all([SMTP_USER, SMTP_PASSWORD, FROM_EMAIL]):
        raise ValueError("Missing email configuration. Check SMTP_USER, SMTP_PASSWORD, and FROM_EMAIL")

    try:
        # Prepare email
        subject = "MecaFlow - Code de vérification"
        body = f"""
Bienvenue sur MecaFlow !

Votre code de vérification est : {code}

Ce code expirera dans 10 minutes.

Cordialement,
L'équipe MecaFlow
        """
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg["To"] = email

        # Configure socket timeout
        socket.setdefaulttimeout(SMTP_TIMEOUT)

        # Create SMTP connection with timeout
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT)
        try:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
            print(f"✓ Code envoyé avec succès à {email}")
            return True
        except smtplib.SMTPAuthenticationError:
            print("✗ Erreur d'authentification SMTP")
            raise ValueError("Échec de l'authentification SMTP")
        except (smtplib.SMTPException, socket.error) as e:
            print(f"✗ Erreur lors de l'envoi: {str(e)}")
            raise ValueError(f"Échec de l'envoi: {str(e)}")
        finally:
            try:
                server.quit()
            except:
                pass
    except Exception as e:
        print(f"✗ Erreur inattendue: {str(e)}")
        raise ValueError(f"Erreur lors de l'envoi: {str(e)}")