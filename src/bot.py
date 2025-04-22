from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ConversationHandler, ContextTypes, CallbackQueryHandler
)
import datetime
import os
from src.config import (
    TELEGRAM_BOT_TOKEN, ADMIN_EMAILS, 
    CATEGORIES, PRIORITIES, GOOGLE_SHEET_ID
)
from src.utils.sheets import store_ticket, get_credentials, get_resolved_tickets, update_ticket_status
from src.utils.email import send_admin_email
import gspread
import logging

# States for conversation
CATEGORY = 0
DESCRIPTION = 1
PRIORITY = 2
CONFIRMATION = 3

class TicketBot:
    # States for conversation
    CATEGORY = 0
    DESCRIPTION = 1
    PRIORITY = 2
    CONFIRMATION = 3

    def __init__(self):
        self.current_ticket = {}
        self.language = 'fr'  # Default language is French only

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commence le processus de création de ticket."""
        logger = logging.getLogger(__name__)
        logger.info("Start command received")

        # Send images first using absolute paths
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
        logger.info(f"Assets directory path: {assets_dir}")

        try:
            pnlp_path = os.path.join(assets_dir, 'pnlp.png')
            commcare_path = os.path.join(assets_dir, 'commcare.png')
            
            logger.info(f"Attempting to send PNLP image from: {pnlp_path}")
            if os.path.exists(pnlp_path):
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(pnlp_path, 'rb'))
                logger.info("PNLP image sent successfully")
            else:
                logger.error(f"PNLP image not found at: {pnlp_path}")
            
            logger.info(f"Attempting to send CommCare image from: {commcare_path}")
            if os.path.exists(commcare_path):
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(commcare_path, 'rb'))
                logger.info("CommCare image sent successfully")
            else:
                logger.error(f"CommCare image not found at: {commcare_path}")

        except Exception as e:
            logger.error(f"Error sending images: {e}", exc_info=True)
            # Continue with the welcome message even if images fail

        welcome_message = (
            "👋 Bienvenue au chatbot de Support de la Campagne MILDA Guinée ! 🇬🇳\n\n"
            "Ce bot est conçu pour vous aider à enregistrer et résoudre les problèmes liés à la campagne MILDA en Guinée.\n\n"
            "Notre objectif est de garantir que toutes les préoccupations soient traitées rapidement et efficacement.\n\n"
            "Pour plus d'informations, contactez DIMAGI \n\n"
            "Veuillez sélectionner la catégorie de votre problème :"
        )

        # Updated problem categories in French
        keyboard = [
            ['Problèmes d\'Utilisateur & d\'Accès', 'Problèmes de Collecte & Soumission de Données'], 
            ['Problèmes de Synchronisation & Connectivité', 'Problèmes de Performance d\'Appareil & d\'Application'],
            ['Problèmes de Rapports & Tableaux de Bord']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

        try:
            await update.message.reply_text(welcome_message, reply_markup=reply_markup)
            logger.info("Welcome message sent successfully")
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}", exc_info=True)
            return ConversationHandler.END

        return CATEGORY

    async def category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stores the category and asks for description."""
        self.current_ticket['category'] = update.message.text
        # Store both username and chat_id
        self.current_ticket['user'] = update.message.from_user.username
        self.current_ticket['chat_id'] = str(update.message.chat_id)
        self.current_ticket['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        await update.message.reply_text(
            'Veuillez décrire votre problème en détail:',
            reply_markup=ReplyKeyboardRemove()
        )
        return DESCRIPTION

    async def description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stores the description and asks for priority."""
        self.current_ticket['description'] = update.message.text
        
        keyboard = [[p] for p in PRIORITIES]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        
        await update.message.reply_text(
            'Veuillez sélectionner le niveau de priorité:',
            reply_markup=reply_markup
        )
        return PRIORITY

    async def priority(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stores the priority and shows confirmation."""
        logger = logging.getLogger(__name__)
        self.current_ticket['priority'] = update.message.text
        
        try:
            # Escape all special characters for MarkdownV2
            category = self.current_ticket['category'].replace('.', '\\.').replace('-', '\\-').replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('!', '\\!')
            description = self.current_ticket['description'].replace('.', '\\.').replace('-', '\\-').replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('!', '\\!')
            priority = self.current_ticket['priority'].replace('.', '\\.').replace('-', '\\-').replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('!', '\\!')
        
            confirmation_text = (
                "Veuillez confirmer les détails de votre ticket\\:\n\n"
                f"*Catégorie*\\: {category}\n"
                f"*Description*\\: {description}\n"
                f"*Priorité*\\: {priority}\n\n"
                "Répondez 'oui' pour confirmer ou 'non' pour annuler\\."
            )
            
            await update.message.reply_text(confirmation_text, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error sending confirmation message: {e}", exc_info=True)
            # Fallback to plain text if Markdown parsing fails
            plain_text = (
                "Veuillez confirmer les détails de votre ticket:\n\n"
                f"Catégorie: {self.current_ticket['category']}\n"
                f"Description: {self.current_ticket['description']}\n"
                f"Priorité: {self.current_ticket['priority']}\n\n"
                "Répondez 'oui' pour confirmer ou 'non' pour annuler."
            )
            await update.message.reply_text(plain_text)
        
        return CONFIRMATION

    async def confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the ticket confirmation and creation."""
        logger = logging.getLogger(__name__)
        
        if update.message.text.lower() in ['oui', 'yes']:
            # Generate a shorter ticket ID (4 characters)
            current_time = int(datetime.datetime.now().strftime('%H%M'))
            ticket_id = f"T{current_time:03d}"  # This will create IDs like T001, T002, etc.
            self.current_ticket['ticket_id'] = ticket_id
            
            try:
                # Store ticket in Google Sheets
                stored = await store_ticket(self.current_ticket)
                if not stored:
                    await update.message.reply_text(
                        "❌ *Erreur lors de la création du ticket\\.*\nVeuillez réessayer plus tard\\.",
                        parse_mode='MarkdownV2'
                    )
                    return ConversationHandler.END
                
                # Send email to admins
                email_sent = await send_admin_email(ADMIN_EMAILS, self.current_ticket)
                if not email_sent:
                    logger.warning(f"Failed to send email notification for ticket {ticket_id}")
                
                # Escape special characters for MarkdownV2
                escaped_ticket_id = ticket_id.replace('-', '\\-')
                
                success_message = (
                    "✅ *Ticket créé avec succès\\!*\n"
                    f"Votre numéro de ticket est\\: *{escaped_ticket_id}*\n\n"
                    f"Pour vérifier le statut\\: /status {escaped_ticket_id}\n"
                    "Pour soumettre un nouveau ticket\\: /start"
                )
                
                await update.message.reply_text(
                    success_message,
                    parse_mode='MarkdownV2'
                )
            except Exception as e:
                logger.error(f"Error in confirm handler: {e}", exc_info=True)
                await update.message.reply_text(
                    "❌ *Une erreur s'est produite\\.*\nVeuillez réessayer plus tard\\.",
                    parse_mode='MarkdownV2'
                )
        else:
            await update.message.reply_text(
                "❌ *Création de ticket annulée\\.*\n"
                "Pour recommencer, utilisez /start",
                parse_mode='MarkdownV2'
            )
        
        self.current_ticket = {}
        return ConversationHandler.END

# Add this function to check ticket status
async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check the status of a ticket."""
    # Extract ticket ID from either command args or message text
    message_text = update.message.text if update.message else ''
    
    if message_text.startswith('/status'):
        # Remove '/status' and any extra spaces from the message
        parts = message_text.split()
        if len(parts) < 2:
            await update.message.reply_text("Veuillez fournir votre numéro de ticket. Exemple: /status <numéro_ticket>")
            return
        ticket_id = parts[1].strip('<>')  # Remove any < > brackets if present
    else:
        await update.message.reply_text("Veuillez fournir votre numéro de ticket. Exemple: /status <numéro_ticket>")
        return
    
    # Authenticate with Google Sheets
    try:
        credentials = get_credentials()
        client = gspread.authorize(credentials)
        
        # Open the Google Sheet
        sheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet("Sheet1")
        
        # Find the ticket
        cell = sheet.find(ticket_id)
        if cell:
            row = sheet.row_values(cell.row)
            # Get column headers to find the correct indices
            headers = sheet.row_values(1)
            
            # Create a dictionary mapping headers to values
            ticket_data = dict(zip(headers, row))
            
            # Format the response message
            response = (
                f"📋 Détails du Ticket:\n\n"
                f"🎫 *Numéro de Ticket*: {ticket_id}\n"
                f"📝 *Catégorie*: {ticket_data.get('category', 'N/A')}\n"
                f"📄 *Description*: {ticket_data.get('description', 'N/A')}\n"
                f"⚡ *Priorité*: {ticket_data.get('priority', 'N/A')}\n"
                f"📊 *Statut*: {ticket_data.get('status', 'N/A')}"
            )
            
            await update.message.reply_text(response, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Numéro de ticket non trouvé.")
    
    except Exception as e:
        print(f"Error checking status: {str(e)}")
        await update.message.reply_text("❌ Erreur lors de la vérification du statut du ticket. Veuillez réessayer plus tard.")

async def check_resolved_tickets(context):
    """Check for resolved tickets and notify users."""
    logger = logging.getLogger(__name__)
    logger.info("Starting check for resolved tickets...")
    
    try:
        # Get resolved tickets
        resolved_tickets, sheet = await get_resolved_tickets()
        if not sheet:
            logger.error("Failed to get sheet reference")
            return
            
        resolved_count = 0
        for ticket in resolved_tickets:
            chat_id = str(ticket.get('chat_id', '')).strip()
            ticket_id = ticket.get('ticket_id', 'NO_ID')
            
            logger.info(f"Processing resolved ticket: {ticket_id}")
            
            keyboard = [
                [
                    InlineKeyboardButton("OUI", callback_data=f"resolved_yes_{ticket_id}"),
                    InlineKeyboardButton("NON", callback_data=f"resolved_no_{ticket_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                # Escape special characters for MarkdownV2
                escaped_ticket_id = ticket_id.replace('-', '\\-')
                category = ticket['category'].replace('.', '\\.').replace('-', '\\-').replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('!', '\\!')
                description = ticket['description'].replace('.', '\\.').replace('-', '\\-').replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('!', '\\!')
                priority = ticket['priority'].replace('.', '\\.').replace('-', '\\-').replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('!', '\\!')
                timestamp = ticket['timestamp'].replace('-', '\\-').replace(':', '\\:')
                
                message = (
                    "🎉 *Mise à jour de votre ticket\\!*\n\n"
                    f"Votre ticket *{escaped_ticket_id}* a été marqué comme résolu par notre équipe\\.\n\n"
                    "*Détails du ticket:*\n"
                    f"📅 *Date de création* : {timestamp}\n"
                    f"📝 *Catégorie* : {category}\n"
                    f"📄 *Description* : {description}\n"
                    f"⚡ *Priorité* : {priority}\n\n"
                    "Est\\-ce que votre problème est effectivement résolu?"
                )
                
                logger.info(f"Attempting to send notification to chat_id: {chat_id}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    reply_markup=reply_markup,
                    parse_mode='MarkdownV2'
                )
                logger.info(f"Successfully sent notification for ticket {ticket_id}")
                
                # Update status to prevent multiple notifications
                logger.info(f"Updating ticket {ticket_id} status to 'En Attente de Confirmation'")
                row_index = resolved_tickets.index(ticket) + 2  # +2 because sheet is 1-indexed and we have headers
                await update_ticket_status(sheet, row_index, 'En Attente de Confirmation')
                resolved_count += 1
                
            except Exception as e:
                logger.error(f"Error sending notification for ticket {ticket_id}: {str(e)}", exc_info=True)
                # Try sending without Markdown as fallback
                try:
                    plain_message = (
                        "🎉 Mise à jour de votre ticket!\n\n"
                        f"Votre ticket {ticket_id} a été marqué comme résolu par notre équipe.\n\n"
                        "Détails du ticket:\n"
                        f"📅 Date de création : {ticket['timestamp']}\n"
                        f"📝 Catégorie : {ticket['category']}\n"
                        f"📄 Description : {ticket['description']}\n"
                        f"⚡ Priorité : {ticket['priority']}\n\n"
                        "Est-ce que votre problème est effectivement résolu?"
                    )
                    logger.info(f"Attempting to send plain text notification for ticket {ticket_id}")
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=plain_message,
                        reply_markup=reply_markup
                    )
                    logger.info(f"Successfully sent plain text notification for ticket {ticket_id}")
                    
                    # Update status even if we had to fall back to plain text
                    row_index = resolved_tickets.index(ticket) + 2
                    await update_ticket_status(sheet, row_index, 'En Attente de Confirmation')
                    resolved_count += 1
                except Exception as e2:
                    logger.error(f"Error sending plain notification for ticket {ticket_id}: {str(e2)}", exc_info=True)
        
        logger.info(f"Completed check. Processed {resolved_count} resolved tickets.")
    except Exception as e:
        logger.error(f"Error in check_resolved_tickets: {str(e)}", exc_info=True)

async def handle_resolution_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the user's confirmation of ticket resolution."""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    response = data[1]  # 'yes' or 'no'
    ticket_id = data[2]
    
    try:
        credentials = get_credentials()
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet("Sheet1")
        
        # Find the ticket
        cell = sheet.find(ticket_id)
        if cell:
            if response == 'yes':
                sheet.update_cell(cell.row, 7, 'Résolu Confirmé')
                try:
                    await query.message.edit_text(
                        "✅ *Ticket Fermé avec Succès*\n\n"
                        "*Merci pour votre confirmation\\.* Votre ticket est maintenant définitivement fermé\\.\n"
                        "Si vous rencontrez un nouveau problème, n'hésitez pas à créer un nouveau ticket avec /start",
                        parse_mode='MarkdownV2'
                    )
                except Exception as e:
                    logger.error(f"Error sending confirmation message: {e}")
                    await query.message.edit_text(
                        "✅ Ticket Fermé avec Succès\n\n"
                        "Merci pour votre confirmation. Votre ticket est maintenant définitivement fermé.\n"
                        "Si vous rencontrez un nouveau problème, n'hésitez pas à créer un nouveau ticket avec /start"
                    )
            else:
                sheet.update_cell(cell.row, 7, 'Ouvert')
                try:
                    await query.message.edit_text(
                        "🔄 *Ticket Rouvert*\n\n"
                        "*Nous avons rouvert votre ticket\\.* Notre équipe va reprendre le traitement dès que possible\\.\n"
                        "Nous vous tiendrons informé de l'avancement\\.",
                        parse_mode='MarkdownV2'
                    )
                except Exception as e:
                    logger.error(f"Error sending reopen message: {e}")
                    await query.message.edit_text(
                        "🔄 Ticket Rouvert\n\n"
                        "Nous avons rouvert votre ticket. Notre équipe va reprendre le traitement dès que possible.\n"
                        "Nous vous tiendrons informé de l'avancement."
                    )
    except Exception as e:
        logger.error(f"Error updating ticket status: {e}", exc_info=True)
        try:
            await query.message.edit_text(
                "*Une erreur s'est produite\\.*\nVeuillez réessayer plus tard\\.",
                parse_mode='MarkdownV2'
            )
        except:
            await query.message.edit_text(
                "Une erreur s'est produite.\nVeuillez réessayer plus tard."
            )

def main():
    """Start the bot."""
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,  # Changed to DEBUG level
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True  # Ensure our logging configuration takes precedence
    )
    logger = logging.getLogger(__name__)

    try:
        # Initialize the application with job queue enabled
        application = (
            Application.builder()
            .token(TELEGRAM_BOT_TOKEN)
            .build()
        )
        logger.info("Created Telegram application")

        # Initialize job queue
        job_queue = application.job_queue
        logger.info("Job queue initialized")

        bot = TicketBot()
        logger.info("Created TicketBot instance")

        # Single conversation handler - removed LANGUAGE state
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', bot.start)],
            states={
                CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.category)],
                DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.description)],
                PRIORITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.priority)],
                CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.confirm)]
            },
            fallbacks=[CommandHandler('status', check_status)]
        )

        # Add handlers
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler('status', check_status))
        application.add_handler(CallbackQueryHandler(handle_resolution_confirmation, pattern="^resolved_"))
        logger.info("Added all handlers")

        # Define error handler
        async def error_handler(update, context):
            """Log the error and send a message to the user."""
            logger.error(f"Exception while handling an update: {context.error}", exc_info=True)
            if update and update.effective_message:
                try:
                    await update.effective_message.reply_text(
                        "Une erreur s'est produite. Veuillez réessayer plus tard."
                    )
                except Exception as e:
                    logger.error(f"Error sending error message: {e}", exc_info=True)

        # Register the error handler
        application.add_error_handler(error_handler)

        # Add job queue for checking resolved tickets
        if job_queue:
            try:
                logger.info("Setting up job queue for checking resolved tickets...")
                
                # Add a one-time job to verify the job queue is working
                async def verify_job_queue(context):
                    logger.info("Job queue verification task running")
                    try:
                        # Test Google Sheets connection
                        credentials = get_credentials()
                        client = gspread.authorize(credentials)
                        sheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet("Sheet1")
                        records = sheet.get_all_records()
                        logger.info(f"Job queue verification: Successfully connected to Google Sheets. Found {len(records)} records.")
                    except Exception as e:
                        logger.error(f"Job queue verification: Error connecting to Google Sheets: {e}", exc_info=True)
                
                # Run verification job after 2 seconds
                job_queue.run_once(verify_job_queue, when=2)
                logger.info("Added verification job")
                
                # Run the main check_resolved_tickets job
                job = job_queue.run_repeating(
                    check_resolved_tickets,
                    interval=30,  # Check every 30 seconds
                    first=5,      # First run after 5 seconds
                    name='check_resolved_tickets'
                )
                logger.info(f"Job queue setup completed successfully. Job: {job.name}, Interval: {job.interval}s")
                
            except Exception as e:
                logger.error(f"Error setting up job queue: {e}", exc_info=True)
        else:
            logger.error("Job queue is not available!")

        # Start the Bot with graceful shutdown
        logger.info("Starting bot...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False  # Prevent the event loop from being closed
        )

    except Exception as e:
        logger.error(f"Critical error in main: {e}", exc_info=True)
        raise  # Re-raise the exception for proper handling

if __name__ == '__main__':
    # Ensure only one instance is running
    import sys
    import os
    import tempfile
    
    # Create a lock file
    lock_file = os.path.join(tempfile.gettempdir(), 'milda_bot.lock')
    
    try:
        # Try to create the lock file
        if os.path.exists(lock_file):
            # Check if the process is still running
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, 0)  # Check if process is running
                print(f"Bot is already running with PID {pid}")
                sys.exit(1)
            except OSError:
                # Process is not running, we can remove the lock file
                os.remove(lock_file)
        
        # Write current PID to lock file
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        
        # Run the bot
        main()
    finally:
        # Clean up lock file when the bot exits
        try:
            if os.path.exists(lock_file):
                os.remove(lock_file)
        except Exception as e:
            print(f"Error removing lock file: {e}")
