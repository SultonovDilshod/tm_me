# utils/timezone_helper.py
import pytz
from datetime import datetime
from typing import Optional

class TimezoneHelper:
    @staticmethod
    def get_valid_timezone(tz_str: str) -> Optional[str]:
        """Validate and return timezone string"""
        try:
            pytz.timezone(tz_str)
            return tz_str
        except pytz.UnknownTimeZoneError:
            return None
    
    @staticmethod
    def get_user_time(user_tz: str) -> datetime:
        """Get current time in user's timezone"""
        try:
            tz = pytz.timezone(user_tz)
            return datetime.now(tz)
        except pytz.UnknownTimeZoneError:
            return datetime.now(pytz.UTC)