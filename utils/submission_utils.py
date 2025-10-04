import os
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Email, To, Content,
    Attachment, FileContent, FileName, FileType, Disposition
)
import logging

logger = logging.getLogger("cad-platform")

async def send_submission_email(file_content, filename, student_email, exercise_title, exercise_type=None):
    """
    Send submission file via SendGrid
    
    Args:
        file_content: The binary content of the file
        filename: Original filename
        student_email: Student's email address
        exercise_title: Title of the exercise
        exercise_type: Type of exercise (to indicate required file type)
    """
    try:
        sender_email = os.getenv("FROM_EMAIL")
        sender_name = os.getenv("FROM_NAME", "Mecaflow Learn")
        receiver_email = os.getenv("TO_EMAIL", "bouiraislam5@gmail.com")
        api_key = os.getenv("SENDGRID_API_KEY")

        if not all([sender_email, api_key, receiver_email]):
            logger.error("Missing required SendGrid configuration")
            return False

        subject = f"Manual Validation Submission - {exercise_title}"

        file_type = ".sldprt" if "part" in exercise_type.lower() else ".sldasm"
        
        body = f"""
        Nouvelle soumission nécessitant une validation manuelle:
        
            Étudiant: {student_email}
            Exercice: {exercise_title}
            Type de fichier requis: {file_type}
            Fichier soumis: {filename}

        Veuillez examiner le fichier ci-joint et valider via la plateforme.
        """

        # Encode file for attachment
        encoded_file = base64.b64encode(file_content).decode()

        # Create attachment
        attachment = Attachment(
            FileContent(encoded_file),
            FileName(filename),
            FileType("application/octet-stream"),
            Disposition("attachment")
        )

        # Create message
        message = Mail(
            from_email=Email(sender_email, sender_name),
            to_emails=To(receiver_email),
            subject=subject,
            plain_text_content=Content("text/plain", body)
        )
        message.attachment = attachment

        # Send email
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        success = response.status_code in [200, 202]
        
        if success:
            logger.info(f"Successfully sent submission email for {student_email}")
        else:
            logger.error(f"Failed to send email. Status code: {response.status_code}")
        
        return success

    except Exception as e:
        logger.error(f"Error sending submission email: {str(e)}")
        return False