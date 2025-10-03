# scheduler/reminder_scheduler.py
import asyncio
from datetime import date, datetime, timedelta
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import logging
from models.birthday import User, Birthday
from utils.timezone_helper import TimezoneHelper
from bot_config import BIRTHDAY_CATEGORIES

logger = logging.getLogger(__name__)

class BirthdayReminder:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=pytz.UTC)
    
    async def check_birthdays_today(self):
        """Check for birthdays today and send reminders"""
        try:
            today = date.today()
            logger.info(f"Checking birthdays for {today}")
            
            # Get all users with birthdays today
            users_with_birthdays = await User.filter(is_deleted=False).prefetch_related('birthdays')
            
            reminder_count = 0
            
            for user in users_with_birthdays:
                user_time = TimezoneHelper.get_user_time(user.timezone)
                user_today = user_time.date()
                
                # Get birthdays for today in user's timezone
                todays_birthdays = [
                    b for b in user.birthdays 
                    if not b.is_deleted
                    and b.birthdate.month == user_today.month 
                    and b.birthdate.day == user_today.day
                ]
                
                if todays_birthdays:
                    await self._send_birthday_reminder(user, todays_birthdays)
                    reminder_count += len(todays_birthdays)
            
            logger.info(f"Sent {reminder_count} birthday reminders")
            
        except Exception as e:
            logger.error(f"Error checking birthdays: {e}")
    
    async def _send_birthday_reminder(self, user: User, birthdays: list):
        """Send enhanced birthday reminder to user"""
        try:
            if len(birthdays) == 1:
                birthday = birthdays[0]
                age = date.today().year - birthday.birthdate.year
                category_display = BIRTHDAY_CATEGORIES.get(birthday.category, birthday.category)
                
                message = (
                    f"🎉 **Birthday Reminder!** 🎂\n\n"
                    f"Today is **{birthday.name}**'s birthday!\n"
                    f"🎈 They are turning **{age} years old** today\n"
                    f"🏷️ Category: {category_display}\n"
                )
                
                if birthday.image_url:
                    message += f"📷 [View Photo]({birthday.image_url})\n"
                
                if birthday.notes:
                    message += f"📝 Notes: {birthday.notes}\n"
                
                message += "\nDon't forget to wish them a happy birthday! 🎈"
                
                # Try to send photo if available
                if birthday.image_url:
                    try:
                        await self.bot.send_photo(
                            user.user_id,
                            birthday.image_url,
                            caption=message
                        )
                    except:
                        # Fallback to text message
                        await self.bot.send_message(user.user_id, message)
                else:
                    await self.bot.send_message(user.user_id, message)
            else:
                message = "🎉 **Birthday Reminders!** 🎂\n\n"
                message += "Today's birthdays:\n\n"
                
                for birthday in birthdays:
                    age = date.today().year - birthday.birthdate.year
                    category_display = BIRTHDAY_CATEGORIES.get(birthday.category, birthday.category)
                    message += f"• **{birthday.name}** (turning {age}) - {category_display}"
                    if birthday.image_url:
                        message += " 📷"
                    if birthday.notes:
                        message += " 📝"
                    message += "\n"
                
                message += "\nDon't forget to wish them happy birthdays! 🎈"
                await self.bot.send_message(user.user_id, message)
            
            logger.info(f"Sent birthday reminder to user {user.user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send reminder to user {user.user_id}: {e}")
    
    async def check_upcoming_birthdays(self):
        """Check for birthdays in next 3 days and send advance notice"""
        try:
            users = await User.filter(is_deleted=False).prefetch_related('birthdays')
            
            for user in users:
                user_time = TimezoneHelper.get_user_time(user.timezone)
                
                upcoming_birthdays = []
                
                for days_ahead in range(1, 4):  # 1-3 days ahead
                    future_date = (user_time + timedelta(days=days_ahead)).date()
                    
                    day_birthdays = [
                        b for b in user.birthdays
                        if not b.is_deleted
                        and b.birthdate.month == future_date.month 
                        and b.birthdate.day == future_date.day
                    ]
                    
                    for birthday in day_birthdays:
                        upcoming_birthdays.append((birthday, days_ahead))
                
                if upcoming_birthdays:
                    await self._send_upcoming_reminder(user, upcoming_birthdays)
            
        except Exception as e:
            logger.error(f"Error checking upcoming birthdays: {e}")
    
    async def _send_upcoming_reminder(self, user: User, upcoming_birthdays: list):
        """Send upcoming birthday reminder with enhanced details"""
        try:
            message = "📅 **Upcoming Birthdays:** 🎂\n\n"
            
            for birthday, days_ahead in upcoming_birthdays:
                age = date.today().year - birthday.birthdate.year + 1
                category_display = BIRTHDAY_CATEGORIES.get(birthday.category, birthday.category)
                
                if days_ahead == 1:
                    day_text = "tomorrow"
                else:
                    day_text = f"in {days_ahead} days"
                
                message += f"• **{birthday.name}** {day_text} (turning {age})\n"
                message += f"  🏷️ {category_display}"
                if birthday.image_url:
                    message += " 📷"
                if birthday.notes:
                    message += " 📝"
                message += "\n\n"
            
            message += "Get ready to celebrate! 🎉"
            
            await self.bot.send_message(user.user_id, message)
            logger.info(f"Sent upcoming birthday reminder to user {user.user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send upcoming reminder to user {user.user_id}: {e}")

    def start(self):
        """Start the scheduler"""
        # Check for birthdays every day at 9 AM
        self.scheduler.add_job(
            self.check_birthdays_today,
            CronTrigger(hour=9, minute=0),
            id='daily_birthday_check',
            name='Daily Birthday Check'
        )
        
        # Check for upcoming birthdays every Sunday at 8 AM
        self.scheduler.add_job(
            self.check_upcoming_birthdays,
            CronTrigger(day_of_week=6, hour=8, minute=0),  # Sunday = 6
            id='weekly_upcoming_check',
            name='Weekly Upcoming Birthdays Check'
        )
        
        self.scheduler.start()
        logger.info("Birthday reminder scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Birthday reminder scheduler stopped")

async def start_scheduler(bot: Bot):
    """Initialize and start the birthday reminder scheduler"""
    reminder = BirthdayReminder(bot)
    reminder.start()
    return reminder