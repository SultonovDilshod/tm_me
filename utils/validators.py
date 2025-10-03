# utils/validators.py
from datetime import datetime, date
from typing import Optional
import re
import validators

class InputValidator:
    @staticmethod
    def parse_date(date_str: str) -> Optional[date]:
        """Parse date string in YYYY-MM-DD format"""
        try:
            # Validate format with regex first
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                return None
            
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Check if date is reasonable (not too far in past/future)
            current_year = datetime.now().year
            if parsed_date.year < 1900 or parsed_date.year > current_year + 50:
                return None
                
            return parsed_date
        except ValueError:
            return None
    
    @staticmethod
    def validate_name(name: str) -> bool:
        """Validate birthday person name"""
        if not name or len(name.strip()) == 0:
            return False
        if len(name.strip()) > 100:
            return False
        # Allow letters, spaces, hyphens, apostrophes
        if not re.match(r'^[a-zA-Z\s\-\'\.]+$', name.strip()):
            return False
        return True
    
    @staticmethod
    def validate_image_url(url: str) -> bool:
        """Validate image URL"""
        if not url:
            return True  # Empty URL is allowed
        
        # Basic URL validation
        if not validators.url(url):
            return False
        
        # Check if URL points to an image
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        url_lower = url.lower()
        
        # Check file extension or common image hosting patterns
        if any(url_lower.endswith(ext) for ext in image_extensions):
            return True
        
        # Common image hosting services
        image_hosts = [
            'imgur.com', 'i.imgur.com',
            'cdn.discordapp.com',
            'pbs.twimg.com',
            'images.unsplash.com',
            'googleusercontent.com',
            'cloudinary.com'
        ]
        
        if any(host in url_lower for host in image_hosts):
            return True
        
        return False
    
    @staticmethod
    def validate_category(category: str) -> bool:
        """Validate birthday category"""
        from bot_config import BIRTHDAY_CATEGORIES
        return category.lower() in BIRTHDAY_CATEGORIES.keys()
