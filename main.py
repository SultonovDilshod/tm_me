# main.py
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from tortoise import Tortoise

from bot_config import BOT_TOKEN, DATABASE_URL
from handlers.user_commands import register_user_handlers
from handlers.admin_commands import register_admin_handlers
from scheduler.reminder_scheduler import start_scheduler
from database.init_db import init_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Main bot entry point"""
    try:
        # Initialize database
        await init_database()
        logger.info("Database initialized successfully")
        
        # Initialize bot and dispatcher
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher(storage=MemoryStorage())
        
        # Register handlers
        register_user_handlers(dp)
        register_admin_handlers(dp)
        
        # Start scheduler
        await start_scheduler(bot)
        logger.info("Scheduler started successfully")
        
        # Start bot
        logger.info("Starting bot...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(main())