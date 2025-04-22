# MILDA Guinea Campaign Support Bot

This Telegram bot helps manage support tickets for the MILDA campaign in Guinea.

## Features

- Ticket creation system for reporting issues
- Categorization of issues by type
- Priority assignment
- Email notifications to administrators
- Ticket status tracking
- Resolution confirmation

## Problem Categories

- Problèmes d'Utilisateur & d'Accès
- Problèmes de Collecte & Soumission de Données
- Problèmes de Synchronisation & Connectivité
- Problèmes de Performance d'Appareil & d'Application
- Problèmes de Rapports & Tableaux de Bord

## Deployment on Render.com

1. Create an account on [Render.com](https://render.com)
2. Connect your GitHub repository
3. Create a new Web Service
4. Set the following environment variables:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - `GOOGLE_SHEET_ID`: Your Google Sheets ID
   - `GOOGLE_SHEETS_CREDENTIALS`: Your Google Sheets credentials JSON

## Environment Variables

Make sure to set these environment variables in Render:

- `TELEGRAM_BOT_TOKEN`: Get from BotFather on Telegram
- `GOOGLE_SHEET_ID`: ID of your Google Sheet
- `GOOGLE_SHEETS_CREDENTIALS`: JSON credentials for Google Sheets API

## Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env` file
4. Run the bot: `python src/bot.py`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
