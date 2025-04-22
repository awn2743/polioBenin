import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Google Sheets Configuration
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
CREDENTIALS_PATH = os.getenv('CREDENTIALS_PATH', 'credentials/google_sheets_credentials.json')

# Email Configuration
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = os.getenv('SMTP_EMAIL')
EMAIL_PASSWORD = os.getenv('SMTP_PASSWORD')

# Admin Emails
ADMIN_EMAILS = [
    'andiaye@dimagi.com',
    'awn2743@gmail.com',
    'abdouliptv@gmail.com'
]

# Categories and Priorities
CATEGORIES = [
    'User & Access Issues',
    'Data Collection & Submission Issues',
    'Sync & Connectivity Issues',
    'Device & App Performance Issues',
    'Reports & Dashboard Issues'
]

PRIORITIES = ['Urgent', 'Moyen', 'Faible']

# Google Sheets Configuration
SHEET_RANGE = 'Sheet1!A:G'  # Adjust based on your sheet structure
