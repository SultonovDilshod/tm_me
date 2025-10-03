# bot_config.py
import os
from dotenv import load_dotenv

load_dotenv()



# Bot Configuration
BOT_TOKEN='7194256042:AAFN3rT4nsnHIwS3fAz_6UOvZxoDl7bWrHw'
SUPERADMIN_ID='6093689347'

# Database Configuration (SQLite)
DATABASE_URL="sqlite://birthday_bot.db"

# Optional Settings
DEFAULT_TIMEZONE='UTC'







# Bot configuration
#BOT_TOKEN = os.getenv('7194256042:AAFN3rT4nsnHIwS3fAz_6UOvZxoDl7bWrHw')
#if not BOT_TOKEN:
#    raise ValueError("BOT_TOKEN not found in environment variables")

# Database configuration (SQLite)
#DATABASE_URL = os.getenv('sqlite://birthday_bot.db', 'sqlite://birthday_bot.db')

# Admin configuration
#SUPERADMIN_ID = int(os.getenv('6093689347', 0))
#if not SUPERADMIN_ID:
#    raise ValueError("SUPERADMIN_ID not found in environment variables")

# Timezone configuration
#DEFAULT_TIMEZONE = os.getenv('UTC', 'UTC')

# Birthday categories
BIRTHDAY_CATEGORIES = {
    'love': '💕 Love',
    'family': '👨‍👩‍👧‍👦 Family', 
    'relative': '👥 Relative',
    'work': '💼 Work',
    'friend': '👫 Friend',
    'other': '🌟 Other'
}