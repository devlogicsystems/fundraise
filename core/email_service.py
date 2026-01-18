"""
Email service for sending emails with attachments.
"""
from django.core.mail import EmailMessage
from django.conf import settings
from .models import CommunicationLog


class EmailService:
    """Service for sending emails to investors."""
    
    def send_draft_email(self, investor, draft, user=None):
        """
        Send an email draft to an investor.
        
        Args:
            investor: Investor model instance
            draft: EmailDraft model instance
            user: User who initiated the send
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Create email
            email = EmailMessage(
                subject=draft.subject,
                body=draft.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[investor.email],
            )
            
            # Set HTML content if body contains HTML tags
            if '<' in draft.body and '>' in draft.body:
                email.content_subtype = 'html'
            
            # Attach artifacts
            for artifact in draft.artifacts.all():
                if artifact.file:
                    try:
                        email.attach_file(artifact.file.path)
                    except Exception as e:
                        print(f"Warning: Could not attach file {artifact.file.path}: {e}")
            
            # Send email
            email.send(fail_silently=False)
            
            # Log communication
            CommunicationLog.objects.create(
                investor=investor,
                draft=draft,
                status='success',
                sent_by=user,
                notes=f"Email sent via chatbot"
            )
            
            return True, "Email sent successfully"
            
        except Exception as e:
            # Log failed communication
            CommunicationLog.objects.create(
                investor=investor,
                draft=draft,
                status='failed',
                sent_by=user,
                notes=f"Failed to send: {str(e)}"
            )
            
            return False, str(e)
    
    def send_custom_email(self, to_email, subject, body, attachments=None, user=None):
        """
        Send a custom email (not from a draft).
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            attachments: List of file paths to attach
            user: User who initiated the send
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
            )
            
            if '<' in body and '>' in body:
                email.content_subtype = 'html'
            
            if attachments:
                for attachment_path in attachments:
                    try:
                        email.attach_file(attachment_path)
                    except Exception as e:
                        print(f"Warning: Could not attach file {attachment_path}: {e}")
            
            email.send(fail_silently=False)
            
            return True, "Email sent successfully"
            
        except Exception as e:
            return False, str(e)
