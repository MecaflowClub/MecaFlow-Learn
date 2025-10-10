import os
import base64
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Email, To, Content,
    Attachment, FileContent, FileName, FileType, Disposition
)
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

# Configuration
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "mecaflowlearn@gmail.com")
FROM_NAME = os.getenv("FROM_NAME", "MecaFlow")
TO_EMAIL = os.getenv("TO_EMAIL", "bouiraislam5@gmail.com")

@dataclass
class EmailError:
    """Structure for email errors"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class EmailService:
    """Service class to handle all email operations"""
    
    def __init__(self):
        if not SENDGRID_API_KEY:
            raise ValueError("SendGrid API key not configured")
        self.client = SendGridAPIClient(SENDGRID_API_KEY)
        self.from_email = Email(FROM_EMAIL, FROM_NAME)
        
    def _create_attachment(self, file_path: str) -> Optional[Attachment]:
        """Create an email attachment from a file"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Attachment file not found: {file_path}")
                return None
                
            with open(file_path, 'rb') as f:
                file_content = f.read()
                encoded_file = base64.b64encode(file_content).decode()
                
            attachment = Attachment()
            attachment.file_content = FileContent(encoded_file)
            attachment.file_name = FileName(os.path.basename(file_path))
            attachment.disposition = Disposition('attachment')
            attachment.file_type = FileType('application/octet-stream')
            return attachment
            
        except Exception as e:
            logger.error(f"Error creating attachment: {str(e)}")
            return None
    
    def send_email(self, to_email: str, subject: str, html_content: str, 
                  attachment_path: Optional[str] = None) -> tuple[bool, Optional[EmailError]]:
        """
        Send an email with optional attachment
        Returns (success, error)
        """
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            if attachment_path:
                attachment = self._create_attachment(attachment_path)
                if attachment:
                    message.attachment = attachment
            
            logger.info(f"Sending email to {to_email}")
            response = self.client.send(message)
            
            if response.status_code not in [200, 202]:
                error = EmailError(
                    code="SEND_FAILED",
                    message=f"Failed to send email. Status: {response.status_code}",
                    details={"status_code": response.status_code}
                )
                logger.error(f"Email send failed: {error.message}")
                return False, error
                
            logger.info(f"Email sent successfully to {to_email}")
            return True, None
            
        except Exception as e:
            error = EmailError(
                code="SEND_ERROR",
                message=str(e),
                details={"error_type": type(e).__name__}
            )
            logger.error(f"Error sending email: {error.message}", exc_info=True)
            return False, error

# Initialize global email service
_email_service = None

def get_email_service() -> EmailService:
    """Get or create the email service singleton"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service

def send_verification_code(email: str, code: str) -> bool:
    """Send a verification code email"""
    html_content = f"""
    <h2>Bienvenue sur MecaFlow Learn!</h2>
    <p>Votre code de vérification est : <strong>{code}</strong></p>
    <p>Ce code expirera dans 10 minutes.</p>
    <br>
    <p>Cordialement,<br>L'équipe MecaFlow</p>
    """
    
    success, error = get_email_service().send_email(
        to_email=email,
        subject="MecaFlow - Code de vérification",
        html_content=html_content
    )
    
    if not success:
        logger.error(f"Failed to send verification code: {error.message if error else 'Unknown error'}")
        
    return success

def send_submission_notification(exercise_name: str, student_email: str, submission_id: str, file_path: str) -> bool:
    """Send notification for manual validation submission"""
    logger.info(f"Sending submission notification for {submission_id}")
    
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
    
    success, error = get_email_service().send_email(
        to_email=TO_EMAIL,
        subject=f"MecaFlow - Nouvelle soumission à valider - {exercise_name}",
        html_content=html_content,
        attachment_path=file_path
    )
    
    if not success:
        logger.error(f"Failed to send submission notification: {error.message if error else 'Unknown error'}")
        
    return success