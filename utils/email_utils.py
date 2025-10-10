from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Email, To, Content, 
    Attachment, FileContent, FileName, FileType, Disposition
)
import os
import base64
import logging
from dotenv import load_dotenv

# Configuration du logging
logger = logging.getLogger(__name__)

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "mecaflowlearn@gmail.com")
FROM_NAME = os.getenv("FROM_NAME", "mecaflow learn")
TO_EMAIL = os.getenv("TO_EMAIL", "bouiraislam5@gmail.com")

def _send_email(subject: str, html_content: str, to_email: str = None, attachment_path: str = None) -> bool:
    """
    Fonction interne unifiée pour l'envoi d'emails
    """
    if not SENDGRID_API_KEY:
        logger.error("SendGrid API key not configured")
        return False

    try:
        message = Mail(
            from_email=Email(FROM_EMAIL, FROM_NAME),
            to_emails=To(to_email or TO_EMAIL),
            subject=subject,
            html_content=Content("text/html", html_content)
        )

        # Ajout de pièce jointe si spécifiée
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                file_content = f.read()
                encoded_file = base64.b64encode(file_content).decode()
            
            attachment = Attachment()
            attachment.file_content = FileContent(encoded_file)
            attachment.file_name = FileName(os.path.basename(attachment_path))
            attachment.disposition = Disposition('attachment')
            attachment.file_type = FileType('application/octet-stream')
            message.attachment = attachment

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        if response.status_code not in [200, 202]:
            logger.error(f"Failed to send email. Status: {response.status_code}")
            return False

        logger.info(f"Email sent successfully to {to_email or TO_EMAIL}")
        return True

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False

def send_verification_code(email: str, code: str) -> bool:
    """
    Envoie un code de vérification par email
    """
    subject = "MecaFlow - Code de vérification"
    html_content = f"""
    <h2>Bienvenue sur MecaFlow Learn!</h2>
    <p>Votre code de vérification est : <strong>{code}</strong></p>
    <p>Ce code expirera dans 10 minutes.</p>
    <br>
    <p>Cordialement,<br>L'équipe MecaFlow</p>
    """
    return _send_email(subject=subject, html_content=html_content, to_email=email)

def send_submission_notification(exercise_name: str, student_email: str, submission_id: str, file_path: str) -> bool:
    """
    Envoie une notification pour une nouvelle soumission d'exercice à validation manuelle
    """
    logger.info(f"Sending submission notification for {submission_id}")
    
    subject = f"MecaFlow - Nouvelle soumission à valider - {exercise_name}"
    html_content = f"""
    <h2>Nouvelle soumission à valider</h2>
    <p>Une nouvelle soumission requiert votre validation :</p>
    <ul>
        <li>Exercice : <strong>{exercise_name}</strong></li>
        <li>Étudiant : <strong>{student_email}</strong></li>
        <li>ID de soumission : <strong>{submission_id}</strong></li>
        <li>Fichier : <strong>{os.path.basename(file_path)}</strong></li>
    </ul>
    <p>Le fichier soumis est attaché à cet email.</p>
    <br>
    <p>Pour valider cette soumission, vous pouvez utiliser l'ID de soumission dans l'interface admin.</p>
    <br>
    <p>Cordialement,<br>{FROM_NAME}</p>
    """
    
    return _send_email(
        subject=subject,
        html_content=html_content,
        attachment_path=file_path
    )

