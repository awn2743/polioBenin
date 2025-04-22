"""
Main entry point for the MILDA Campaign Support Bot.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging first
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Setup environment and Python path."""
    try:
        # Get the absolute path of the current file
        current_file = Path(__file__).resolve()
        project_root = current_file.parent

        # Add project root to Python path if not already there
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
            logger.info(f"Added {project_root} to Python path")

        # Log environment information
        logger.info(f"Python path: {sys.path}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Project root: {project_root}")
        logger.info(f"Environment variables: {sorted(os.environ.keys())}")

        # Map environment variables to handle different naming conventions
        env_vars = {
            'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
            'GOOGLE_SHEET_ID': os.getenv('GOOGLE_SHEET_ID'),
            'GOOGLE_SHEETS_CREDENTIALS': os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON') or os.getenv('GOOGLE_SHEETS_CREDENTIALS'),
            'ADMIN_EMAILS': os.getenv('ADMIN_EMAILS'),
            'SMTP_EMAIL': os.getenv('SMTP_EMAIL'),
            'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD')
        }
        
        # Check for missing variables
        missing_vars = [key for key, value in env_vars.items() if not value]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        # Set environment variables with standardized names
        for key, value in env_vars.items():
            if value:
                os.environ[key] = value
                logger.info(f"Set environment variable: {key}")

    except Exception as e:
        logger.error(f"Error setting up environment: {e}", exc_info=True)
        sys.exit(1)

def main():
    """Start the bot."""
    try:
        # Setup environment first
        setup_environment()
        
        # Import dependencies after environment is set up
        from telegram import Update
        from telegram.ext import (
            Application, CommandHandler, MessageHandler, 
            filters, ConversationHandler, CallbackQueryHandler
        )
        from src.bot import (
            TicketBot, check_status, 
            handle_resolution_confirmation, 
            check_resolved_tickets
        )
        from src.config import TELEGRAM_BOT_TOKEN

        # Log successful imports
        logger.info("Successfully imported all required modules")
        
        # Create the Application
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        logger.info("Created Telegram application")

        # Create an instance of the bot
        bot = TicketBot()
        logger.info("Created TicketBot instance")

        # Create conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', bot.start)],
            states={
                0: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.category)],
                1: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.description)],
                2: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.priority)],
                3: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.confirm)],
            },
            fallbacks=[],
        )

        # Add handlers
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler('status', check_status))
        application.add_handler(CallbackQueryHandler(handle_resolution_confirmation, pattern='^resolved_'))
        logger.info("Added all handlers")

        # Add job for checking resolved tickets
        try:
            job_queue = application.job_queue
            if job_queue:
                job_queue.run_repeating(check_resolved_tickets, interval=3600)  # Check every hour
                logger.info("Added job queue for checking resolved tickets")
            else:
                logger.warning("Job queue is not available. Periodic ticket checking will not work.")
        except Exception as e:
            logger.error(f"Error setting up job queue: {e}", exc_info=True)
            logger.warning("Continuing without job queue functionality")

        # Start the Bot
        logger.info("Starting bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main() 