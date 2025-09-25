import smtplib
from email.mime.text import MIMEText
import os
import socket
import time
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.sendgrid.net")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", "mecaflowlearn@gmail.com")
FROM_NAME = os.getenv("FROM_NAME", "MecaFlow")

# Configuration
SMTP_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

def send_verification_code(email: str, code: str):
    if not all([SMTP_USER, SMTP_PASSWORD, FROM_EMAIL]):
        raise ValueError("Missing email configuration. Check SMTP_USER, SMTP_PASSWORD, and FROM_EMAIL")

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            print(f"Tentative d'envoi {attempt + 1}/{MAX_RETRIES}")
            
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

            print(f"Connexion à {SMTP_SERVER}:{SMTP_PORT}...")
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT)
            
            try:
                print("Configuration TLS...")
                server.starttls()
                
                print("Authentification...")
                server.login(SMTP_USER, SMTP_PASSWORD)
                
                print("Envoi du message...")
                server.send_message(msg)
                
                print(f"✓ Code envoyé avec succès à {email}")
                return True
                
            except socket.timeout:
                print(f"Timeout lors de la tentative {attempt + 1}")
                last_error = "Connection timed out"
                
            except smtplib.SMTPAuthenticationError as auth_err:
                print(f"Erreur d'authentification: {auth_err}")
                raise ValueError(f"Authentication failed: {auth_err}")
                
            except smtplib.SMTPException as smtp_err:
                print(f"Erreur SMTP: {smtp_err}")
                last_error = f"SMTP error: {smtp_err}"
                
            finally:
                try:
                    server.quit()
                except:
                    pass
                    
        except Exception as e:
            print(f"Erreur lors de la tentative {attempt + 1}: {str(e)}")
            last_error = str(e)
            
        if attempt < MAX_RETRIES - 1:
            print(f"Attente de {RETRY_DELAY} secondes avant la prochaine tentative...")
            time.sleep(RETRY_DELAY)
            
    # Si toutes les tentatives ont échoué
    raise ValueError(f"Failed after {MAX_RETRIES} attempts. Last error: {last_error}")