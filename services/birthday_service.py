# services/birthday_service.py
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from models.birthday import User, Birthday
from utils.validators import InputValidator
from bot_config import BIRTHDAY_CATEGORIES
import calendar

class BirthdayService:
    @staticmethod
    async def add_birthday(
        user_id: int, 
        name: str, 
        birthdate_str: str, 
        category: str = 'other',
        image_url: str = None,
        notes: str = None
    ) -> Dict[str, Any]:
        """Add a birthday for a user"""
        try:
            # Validate inputs
            if not InputValidator.validate_name(name):
                return {"success": False, "message": "Invalid name format"}
            
            birthdate = InputValidator.parse_date(birthdate_str)
            if not birthdate:
                return {"success": False, "message": "Invalid date format. Use YYYY-MM-DD"}
            
            if not InputValidator.validate_category(category):
                return {"success": False, "message": f"Invalid category. Use: {', '.join(BIRTHDAY_CATEGORIES.keys())}"}
            
            if image_url and not InputValidator.validate_image_url(image_url):
                return {"success": False, "message": "Invalid image URL format"}
            
            # Get or create user
            user, _ = await User.get_or_create(user_id=user_id)
            
            # Check if birthday already exists (including deleted ones)
            existing = await Birthday.filter(user=user, name__iexact=name.strip()).first()
            if existing and not existing.is_deleted:
                return {"success": False, "message": f"Birthday for {name} already exists"}
            elif existing and existing.is_deleted:
                # Restore deleted birthday with new data
                existing.birthdate = birthdate
                existing.category = category.lower()
                existing.image_url = image_url
                existing.notes = notes
                existing.is_deleted = False
                existing.deleted_at = None
                existing.updated_at = datetime.now()
                await existing.save()
                
                return {
                    "success": True,
                    "message": f"Birthday restored for {existing.name} ({birthdate})",
                    "birthday": existing
                }
            
            # Create new birthday
            birthday = await Birthday.create(
                user=user,
                name=name.strip().title(),
                birthdate=birthdate,
                category=category.lower(),
                image_url=image_url,
                notes=notes
            )
            
            category_display = BIRTHDAY_CATEGORIES.get(category.lower(), category)
            return {
                "success": True, 
                "message": f"Birthday added for {birthday.name} ({birthdate}) - Category: {category_display}",
                "birthday": birthday
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error adding birthday: {str(e)}"}
    
    @staticmethod
    async def delete_birthday(user_id: int, name: str) -> Dict[str, Any]:
        """Soft delete a birthday for a user"""
        try:
            user = await User.get_or_none(user_id=user_id)
            if not user:
                return {"success": False, "message": "User not found"}
            
            birthday = await Birthday.filter(
                user=user, 
                name__iexact=name.strip(),
                is_deleted=False
            ).first()
            if not birthday:
                return {"success": False, "message": f"Birthday for {name} not found"}
            
            # Soft delete
            birthday.is_deleted = True
            birthday.deleted_at = datetime.now()
            await birthday.save()
            
            return {"success": True, "message": f"Birthday for {name} deleted"}
            
        except Exception as e:
            return {"success": False, "message": f"Error deleting birthday: {str(e)}"}
    
    @staticmethod
    async def update_birthday(
        user_id: int, 
        name: str, 
        new_date_str: str = None,
        new_category: str = None,
        new_image_url: str = None,
        new_notes: str = None
    ) -> Dict[str, Any]:
        """Update a birthday for a user"""
        try:
            user = await User.get_or_none(user_id=user_id)
            if not user:
                return {"success": False, "message": "User not found"}
            
            birthday = await Birthday.filter(
                user=user, 
                name__iexact=name.strip(),
                is_deleted=False
            ).first()
            if not birthday:
                return {"success": False, "message": f"Birthday for {name} not found"}
            
            # Update fields if provided
            updated_fields = []
            
            if new_date_str:
                new_date = InputValidator.parse_date(new_date_str)
                if not new_date:
                    return {"success": False, "message": "Invalid date format. Use YYYY-MM-DD"}
                birthday.birthdate = new_date
                updated_fields.append(f"date to {new_date}")
            
            if new_category:
                if not InputValidator.validate_category(new_category):
                    return {"success": False, "message": f"Invalid category. Use: {', '.join(BIRTHDAY_CATEGORIES.keys())}"}
                birthday.category = new_category.lower()
                updated_fields.append(f"category to {BIRTHDAY_CATEGORIES.get(new_category.lower())}")
            
            if new_image_url is not None:  # Allow empty string to remove image
                if new_image_url and not InputValidator.validate_image_url(new_image_url):
                    return {"success": False, "message": "Invalid image URL format"}
                birthday.image_url = new_image_url if new_image_url else None
                updated_fields.append("image")
            
            if new_notes is not None:
                birthday.notes = new_notes if new_notes else None
                updated_fields.append("notes")
            
            await birthday.save()
            
            updates_text = ", ".join(updated_fields) if updated_fields else "no changes"
            return {
                "success": True, 
                "message": f"Birthday for {name} updated: {updates_text}"
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error updating birthday: {str(e)}"}
    
    @staticmethod
    async def get_user_birthdays(user_id: int, include_deleted: bool = False) -> List[Birthday]:
        """Get all birthdays for a user"""
        user = await User.get_or_none(user_id=user_id)
        if not user:
            return []
        
        if include_deleted:
            return await Birthday.filter(user=user).order_by('birthdate')
        else:
            return await Birthday.filter(user=user, is_deleted=False).order_by('birthdate')
    
    @staticmethod
    async def get_birthdays_by_category(user_id: int, category: str) -> List[Birthday]:
        """Get birthdays for a specific category"""
        if not InputValidator.validate_category(category):
            return []
        
        user = await User.get_or_none(user_id=user_id)
        if not user:
            return []
        
        return await Birthday.filter(
            user=user,
            category=category.lower(),
            is_deleted=False
        ).order_by('birthdate')
    
    @staticmethod
    async def get_birthdays_by_month(user_id: int, month: int) -> List[Birthday]:
        """Get birthdays for a specific month"""
        if month < 1 or month > 12:
            return []
        
        user = await User.get_or_none(user_id=user_id)
        if not user:
            return []
        
        return await Birthday.filter(
            user=user, 
            birthdate__month=month,
            is_deleted=False
        ).order_by('birthdate__day')
    
    @staticmethod
    async def get_user_stats(user_id: int) -> Dict[str, Any]:
        """Get comprehensive user statistics using pandas-like analysis"""
        user = await User.get_or_none(user_id=user_id)
        if not user:
            return {}
        
        # Get all active birthdays
        birthdays = await Birthday.filter(user=user, is_deleted=False)
        total_count = len(birthdays)
        
        if total_count == 0:
            return {
                "total_birthdays": 0,
                "upcoming_this_month": 0,
                "next_birthday": None,
                "category_breakdown": {},
                "monthly_distribution": {},
                "average_age": 0
            }
        
        current_date = date.today()
        current_month = current_date.month
        current_year = current_date.year
        
        # Category analysis
        category_counts = {}
        for birthday in birthdays:
            cat = birthday.category
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Monthly distribution
        monthly_counts = {}
        for i in range(1, 13):
            monthly_counts[calendar.month_name[i]] = 0
        
        for birthday in birthdays:
            month_name = calendar.month_name[birthday.birthdate.month]
            monthly_counts[month_name] += 1
        
        # Age analysis
        ages = []
        for birthday in birthdays:
            age = current_year - birthday.birthdate.year
            # Adjust if birthday hasn't occurred this year
            if (birthday.birthdate.month, birthday.birthdate.day) > (current_date.month, current_date.day):
                age -= 1
            ages.append(age)
        
        average_age = sum(ages) / len(ages) if ages else 0
        
        # Upcoming birthdays this month
        upcoming_this_month = sum(1 for b in birthdays 
                                 if b.birthdate.month == current_month 
                                 and b.birthdate.day >= current_date.day)
        
        # Find next birthday
        next_birthday = None
        min_days = float('inf')
        
        for birthday in birthdays:
            # Calculate days until next occurrence
            this_year = current_date.replace(
                month=birthday.birthdate.month, 
                day=birthday.birthdate.day
            )
            
            if this_year < current_date:
                this_year = this_year.replace(year=current_date.year + 1)
            
            days_until = (this_year - current_date).days
            
            if days_until < min_days:
                min_days = days_until
                next_birthday = {
                    "name": birthday.name,
                    "date": birthday.birthdate,
                    "days_until": days_until,
                    "category": birthday.category
                }
        
        return {
            "total_birthdays": total_count,
            "upcoming_this_month": upcoming_this_month,
            "next_birthday": next_birthday,
            "category_breakdown": category_counts,
            "monthly_distribution": monthly_counts,
            "average_age": round(average_age, 1),
            "age_range": {
                "min": min(ages) if ages else 0,
                "max": max(ages) if ages else 0
            }
        }
    
    @staticmethod
    async def restore_deleted_birthday(user_id: int, name: str) -> Dict[str, Any]:
        """Restore a soft deleted birthday"""
        try:
            user = await User.get_or_none(user_id=user_id)
            if not user:
                return {"success": False, "message": "User not found"}
            
            birthday = await Birthday.filter(
                user=user,
                name__iexact=name.strip(),
                is_deleted=True
            ).first()
            
            if not birthday:
                return {"success": False, "message": f"No deleted birthday found for {name}"}
            
            birthday.is_deleted = False
            birthday.deleted_at = None
            birthday.updated_at = datetime.now()
            await birthday.save()
            
            return {"success": True, "message": f"Birthday for {name} restored successfully"}
            
        except Exception as e:
            return {"success": False, "message": f"Error restoring birthday: {str(e)}"}