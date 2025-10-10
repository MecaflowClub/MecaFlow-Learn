from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Email, To, Content,
    Attachment, FileContent, FileName, FileType, Disposition
)
import os
import base64
from dotenv import load_dotenv

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "mecaflowlearn@gmail.com")
FROM_NAME = os.getenv("FROM_NAME", "MecaFlow")
TO_EMAIL = os.getenv("TO_EMAIL", "bouiraislam5@gmail.com")

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
        print(f"Attempting to send email with API key: {SENDGRID_API_KEY[:10]}...")
        response = sg.send(message)
        
        if response.status_code == 403:
            print("403 Forbidden - Please check: ")
            print("1. API key has 'Mail Send' permission")
            print("2. Sender email is verified")
            print("3. API key is valid and not revoked")
            raise ValueError("SendGrid authentication failed - check API key permissions")
            
        if response.status_code not in [200, 202]:
            raise ValueError(f"SendGrid API error: {response.status_code}")
            
        print(f"Email sent successfully. Status code: {response.status_code}")
        return True

    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg:
            print("Authentication failed with SendGrid API")
        print(f"Error sending email: {error_msg}")
        raise ValueError(f"Failed to send email: {error_msg}")

def send_submission_notification(exercise_name: str, student_email: str, submission_id: str, file_path: str):
    """Send notification for manual validation submission"""
    print("\n=== Starting Email Notification Process ===")
    print(f"SENDGRID_API_KEY present: {bool(SENDGRID_API_KEY)}")
    print(f"FROM_EMAIL: {FROM_EMAIL}")
    print(f"TO_EMAIL: {TO_EMAIL}")
    print(f"File path: {file_path}")
    print(f"File exists: {os.path.exists(file_path)}")
    
    if not SENDGRID_API_KEY:
        raise ValueError("SendGrid API key not configured")

    try:
        print("\nCreating email message...")
        # Create message
        message = Mail(
            from_email=Email(FROM_EMAIL, FROM_NAME),
            to_emails=To(TO_EMAIL),
            subject=f"MecaFlow - Nouvelle soumission à valider - {exercise_name}",
            html_content=Content(
                "text/html",
                f"""
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
            )
        )

        # Add attachment if file exists
        print("\nProcessing attachment...")
        if os.path.exists(file_path):
            print(f"Reading file: {file_path}")
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                    file_size = len(file_content)
                    print(f"File size: {file_size} bytes")
                    encoded_file = base64.b64encode(file_content).decode()
                
                print("Creating attachment object...")
                attachment = Attachment()
                attachment.file_content = FileContent(encoded_file)
                attachment.file_name = FileName(os.path.basename(file_path))
                attachment.disposition = Disposition('attachment')
                attachment.file_type = FileType('application/octet-stream')
                message.attachment = attachment
                print(f"File attached successfully: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Error processing attachment: {str(e)}")
                raise
        else:
            print(f"Warning: File not found at {file_path}")

        # Send via SendGrid API
        print("\nInitializing SendGrid client...")
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        print(f"Attempting to send notification to {TO_EMAIL}")
        
        try:
            print("Sending email...")
            response = sg.send(message)
            print(f"Response status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response body: {response.body.decode() if response.body else 'No body'}")
            
            if response.status_code == 403:
                print("\n403 Forbidden - Please check:")
                print("1. API key has 'Mail Send' permission")
                print("2. Sender email is verified")
                print("3. API key is valid and not revoked")
                raise ValueError("SendGrid authentication failed - check API key permissions")
                
            if response.status_code not in [200, 202]:
                print(f"\nUnexpected status code: {response.status_code}")
                raise ValueError(f"SendGrid API error: {response.status_code}")
                
            print("\nNotification email sent successfully!")
            return True
            
        except Exception as e:
            print(f"\nError during send operation: {str(e)}")
            raise

    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg:
            print("Authentication failed with SendGrid API")
        print(f"Error sending notification email: {error_msg}")
        raise ValueError(f"Failed to send notification email: {error_msg}")