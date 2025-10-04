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
        # Get and verify environment variables
        sender_email = os.getenv("FROM_EMAIL")
        sender_name = os.getenv("FROM_NAME", "Mecaflow Learn")
        receiver_email = os.getenv("TO_EMAIL", "bouiraislam5@gmail.com")
        api_key = os.getenv("SENDGRID_API_KEY")

        # Log configuration status
        logger.info(f"Email Configuration:")
        logger.info(f"- Sender: {sender_email} ({sender_name})")
        logger.info(f"- Receiver: {receiver_email}")
        logger.info(f"- API Key present: {'Yes' if api_key else 'No'}")

        if not all([sender_email, api_key, receiver_email]):
            missing = []
            if not sender_email: missing.append("FROM_EMAIL")
            if not api_key: missing.append("SENDGRID_API_KEY")
            if not receiver_email: missing.append("TO_EMAIL")
            logger.error(f"Missing required SendGrid configuration: {', '.join(missing)}")
            return False

        subject = f"Manual Validation Submission - {exercise_title}"

        # Default to part if exercise_type is None
        exercise_type = exercise_type or "part"
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

    except SendGridAPIClient.AuthenticationError as e:
        logger.error(f"SendGrid authentication failed: {str(e)}")
        logger.error("Please verify your SENDGRID_API_KEY environment variable")
        return False
    except SendGridAPIClient.APIError as e:
        logger.error(f"SendGrid API error: {str(e)}")
        logger.error(f"Response status code: {getattr(e, 'status_code', 'N/A')}")
        logger.error(f"Response body: {getattr(e, 'body', 'N/A')}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending submission email: {str(e)}")
        logger.exception("Full error traceback:")
        return False