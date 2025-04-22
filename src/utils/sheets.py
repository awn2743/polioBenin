import os
import json
import asyncio
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
import gspread
from googleapiclient.discovery import build
import logging
from functools import wraps
import time

# Configure logging
logger = logging.getLogger(__name__)

SHEET_RANGE = "A:H"  # Assuming columns A through H are used

# Rate limiting settings
MAX_REQUESTS_PER_MINUTE = 50  # Keep below Google Sheets limit
_request_timestamps = []
_lock = asyncio.Lock()

def rate_limit():
    """Rate limiting decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with _lock:
                current_time = time.time()
                # Remove timestamps older than 1 minute
                global _request_timestamps
                _request_timestamps = [ts for ts in _request_timestamps if current_time - ts < 60]
                
                if len(_request_timestamps) >= MAX_REQUESTS_PER_MINUTE:
                    wait_time = 60 - (current_time - _request_timestamps[0])
                    if wait_time > 0:
                        logger.warning(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                        await asyncio.sleep(wait_time)
                
                _request_timestamps.append(current_time)
                
                # Execute the async function
                return await func(*args, **kwargs)
        return wrapper
    return decorator

def get_credentials():
    """Get Google Sheets credentials from environment variable."""
    try:
        # Try both possible environment variable names
        creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS') or os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON')
        if not creds_json:
            raise ValueError("Google Sheets credentials not found in environment variables")
        
        logger.info("Found Google Sheets credentials in environment variables")
        
        try:
            creds_dict = json.loads(creds_json)
            logger.info("Successfully parsed Google Sheets credentials JSON")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Google Sheets credentials JSON: {e}")
            raise ValueError("Invalid Google Sheets credentials JSON format")
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://spreadsheets.google.com/feeds',
                   'https://www.googleapis.com/auth/spreadsheets',
                   'https://www.googleapis.com/auth/drive']
        )
        logger.info("Successfully created Google Sheets credentials")
        return credentials
        
    except Exception as e:
        logger.error(f"Error getting credentials: {e}", exc_info=True)
        raise

@rate_limit()
async def store_ticket(ticket_data):
    """Store ticket data in Google Sheets."""
    try:
        credentials = get_credentials()
        client = gspread.authorize(credentials)
        logger.info("Successfully authorized with Google Sheets")
        
        # Open the Google Sheet
        sheet = client.open_by_key(os.getenv('GOOGLE_SHEET_ID')).worksheet("Sheet1")
        logger.info("Successfully opened Google Sheet")
        
        # Prepare row data
        row = [
            ticket_data['ticket_id'],
            ticket_data['timestamp'],
            ticket_data.get('chat_id', ''),  # Chat ID for notifications
            ticket_data['category'],
            ticket_data['description'],
            ticket_data['priority'],
            'Ouvert'  # Initial status in French
        ]
        
        # Append the row
        await asyncio.get_event_loop().run_in_executor(None, sheet.append_row, row)
        logger.info(f"Successfully stored ticket {ticket_data['ticket_id']}")
        return True
    except Exception as e:
        logger.error(f"Error storing ticket: {e}", exc_info=True)
        return False

@rate_limit()
async def get_resolved_tickets():
    """Get all resolved tickets from Google Sheets."""
    try:
        credentials = get_credentials()
        client = gspread.authorize(credentials)
        logger.info("Successfully authorized with Google Sheets")
        
        # Open the Google Sheet
        sheet = client.open_by_key(os.getenv('GOOGLE_SHEET_ID')).worksheet("Sheet1")
        logger.info("Successfully opened Google Sheet")
        
        # Get all records
        records = await asyncio.get_event_loop().run_in_executor(None, sheet.get_all_records)
        logger.info(f"Retrieved {len(records)} tickets from Google Sheets")
        
        # Filter for resolved tickets (handle both English and French status)
        resolved_tickets = [
            ticket for ticket in records 
            if str(ticket.get('status', '')).strip() in ['Resolved', 'Résolu']
            and ticket.get('chat_id')
        ]
        
        logger.info(f"Found {len(resolved_tickets)} resolved tickets")
        return resolved_tickets, sheet
        
    except Exception as e:
        logger.error(f"Error getting resolved tickets: {e}", exc_info=True)
        return [], None

@rate_limit()
async def update_ticket_status(sheet, row_index, new_status):
    """Update ticket status in Google Sheets."""
    try:
        status_column = 7  # Assuming status is in column G (7)
        await asyncio.get_event_loop().run_in_executor(
            None, 
            sheet.update_cell,
            row_index,
            status_column,
            new_status
        )
        logger.info(f"Updated ticket status to {new_status} at row {row_index}")
        return True
    except Exception as e:
        logger.error(f"Error updating ticket status: {e}", exc_info=True)
        return False
