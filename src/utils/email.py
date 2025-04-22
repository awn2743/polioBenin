import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, GOOGLE_SHEET_ID, ADMIN_EMAILS
import logging

# Configure logging
logger = logging.getLogger(__name__)

async def send_admin_email(admin_emails, ticket_data):
    """Sends notification email to all admins."""
    sheet_url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}"
    
    msg = MIMEText(
        f"Campagne MILDA SUPPORT - Nouveau ticket créé:\n\n"
        f"Numéro de Ticket: {ticket_data['ticket_id']}\n"
        f"Catégorie: {ticket_data['category']}\n"
        f"Description: {ticket_data['description']}\n"
        f"Priorité: {ticket_data['priority']}\n"
        f"Chat ID: {ticket_data.get('chat_id', 'N/A')}\n\n"
        f"Voir tous les tickets ici: {sheet_url}"
    )
    
    msg['Subject'] = f"Nouveau Ticket: {ticket_data['ticket_id']}"
    msg['From'] = EMAIL_USER
    msg['To'] = ', '.join(admin_emails)  # Join all admin emails
    
    try:
        # Run email sending in a thread pool to not block
        await asyncio.get_event_loop().run_in_executor(None, _send_email, msg)
        logger.info(f"Successfully sent email notification for ticket {ticket_data['ticket_id']} to all admins")
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}", exc_info=True)
        return False

def _send_email(msg):
    """Helper function to send email synchronously."""
    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
            logger.info("Email sent successfully")
    except Exception as e:
        logger.error(f"Error in _send_email: {e}", exc_info=True)
        raise
