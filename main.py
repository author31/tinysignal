import asyncio

from telegram import InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

from app.config import secrets, settings
from app.logger import setup_logger
from app.repositories.cluster import ClusterRepository
from app.services import crawler
from app.services.telegram import (get_telegram_cluster_posts,
                                   get_telegram_hot_news,
                                   handle_telegram_callback)

logger = setup_logger(__name__)

cluster_repo = ClusterRepository()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    welcome_text = "Welcome to TinySignal Bot!\n\nUse /hotnews to see trending news clusters from Hacker News."
    await update.message.reply_text(welcome_text)

async def hot_news_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /hotnews command to display trending clusters."""
    try:
        response = get_telegram_hot_news()
        await update.message.reply_text(
            text=response["text"],
            reply_markup=InlineKeyboardMarkup(response["reply_markup"]["inline_keyboard"])
        )
    except Exception as e:
        logger.error(f"Error in hot_news_command: {e}", exc_info=True)
        await update.message.reply_text("❌ Error fetching hot news. Please try again later.")

async def scheduled_crawler(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run crawler job every hour."""
    try:
        logger.info("Running scheduled crawler job...")
        # crawler.fetch_and_insert() is sync, so run in thread pool
        await asyncio.get_event_loop().run_in_executor(None, crawler.fetch_and_insert)
        logger.info("Scheduled crawler job completed")
    except Exception as e:
        logger.error(f"Error in scheduled crawler: {e}", exc_info=True)

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline buttons."""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query
    
    try:
        response = handle_telegram_callback(query.data)
        await query.edit_message_text(
            text=response["text"],
            reply_markup=InlineKeyboardMarkup(response["reply_markup"]["inline_keyboard"])
        )
    except Exception as e:
        logger.error(f"Error in button_callback_handler: {e}", exc_info=True)
        await query.edit_message_text("❌ Error processing your request. Please try again.")

async def shutdown_handler(app: Application) -> None:
    """Handle graceful shutdown."""
    logger.info("Shutting down bot...")
    # Add any cleanup code here if needed

def init_app():
    if not cluster_repo.is_persistent_path_exists():
        cluster_repo.create_embeddings_table()
        cluster_repo.create_cluster_table()
        cluster_repo.create_cluster_title_table()

def main():
    assert "TELEGRAM_BOT_TOKEN" in secrets.keys(), "Missing TELEGRAM_BOT_TOKEN."
    
    init_app()
    
    application = Application.builder().token(secrets["TELEGRAM_BOT_TOKEN"]).build()
    job_queue = application.job_queue
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("hotnews", hot_news_command))
    
    # Add callback handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_callback_handler))
    
    # Schedule crawler job every hour
    # job_queue.run_repeating(scheduled_crawler, interval=3600, first=10)
    
    try:
        logger.info("Starting bot with job queue...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down gracefully...")
    except Exception as e:
        logger.critical(f"CRITICAL: Failed to initialize or run the Telegram bot: {e}", exc_info=True)


if __name__ == "__main__":
    main()
