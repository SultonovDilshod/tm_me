# services/admin_service.py
import csv
import io
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, date
from models.birthday import User, Birthday
from bot_config import BIRTHDAY_CATEGORIES

class AdminService:
    @staticmethod
    async def get_all_birthdays(include_deleted: bool = False) -> List[Dict[str, Any]]:
        """Get all birthdays from all users"""
        if include_deleted:
            birthdays = await Birthday.all().prefetch_related('user')
        else:
            birthdays = await Birthday.filter(is_deleted=False).prefetch_related('user')
        
        result = []
        for birthday in birthdays:
            result.append({
                "id": birthday.id,
                "user_id": birthday.user.user_id,
                "username": birthday.user.username,
                "name": birthday.name,
                "birthdate": birthday.birthdate,
                "category": birthday.category,
                "image_url": birthday.image_url,
                "notes": birthday.notes,
                "created_at": birthday.created_at,
                "is_deleted": birthday.is_deleted,
                "deleted_at": birthday.deleted_at
            })
        
        return result
    
    @staticmethod
    async def export_to_csv(include_deleted: bool = False) -> io.StringIO:
        """Export all birthdays to CSV format"""
        birthdays = await AdminService.get_all_birthdays(include_deleted)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'User ID', 'Username', 'Birthday Name', 
            'Birth Date', 'Category', 'Image URL', 'Notes',
            'Created At', 'Is Deleted', 'Deleted At'
        ])
        
        # Write data
        for birthday in birthdays:
            writer.writerow([
                birthday['id'],
                birthday['user_id'],
                birthday['username'] or 'N/A',
                birthday['name'],
                birthday['birthdate'].strftime('%Y-%m-%d'),
                BIRTHDAY_CATEGORIES.get(birthday['category'], birthday['category']),
                birthday['image_url'] or 'N/A',
                birthday['notes'] or 'N/A',
                birthday['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                'Yes' if birthday['is_deleted'] else 'No',
                birthday['deleted_at'].strftime('%Y-%m-%d %H:%M:%S') if birthday['deleted_at'] else 'N/A'
            ])
        
        output.seek(0)
        return output
    
    @staticmethod
    async def get_analytics_report() -> Dict[str, Any]:
        """Generate comprehensive analytics using pandas-like analysis"""
        try:
            # Get all birthdays (including deleted for full analysis)
            all_birthdays = await AdminService.get_all_birthdays(include_deleted=True)
            active_birthdays = await AdminService.get_all_birthdays(include_deleted=False)
            
            if not all_birthdays:
                return {"error": "No data available for analysis"}
            
            # Convert to DataFrame-like structure for analysis
            df_data = []
            for birthday in all_birthdays:
                current_year = datetime.now().year
                age = current_year - birthday['birthdate'].year
                if (birthday['birthdate'].month, birthday['birthdate'].day) > (datetime.now().month, datetime.now().day):
                    age -= 1
                
                df_data.append({
                    'user_id': birthday['user_id'],
                    'category': birthday['category'],
                    'age': age,
                    'birth_month': birthday['birthdate'].month,
                    'is_deleted': birthday['is_deleted'],
                    'has_image': bool(birthday['image_url']),
                    'has_notes': bool(birthday['notes'])
                })
            
            # Analysis
            total_users = len(set(b['user_id'] for b in all_birthdays))
            total_birthdays = len(all_birthdays)
            active_birthdays_count = len(active_birthdays)
            deleted_birthdays_count = total_birthdays - active_birthdays_count
            
            # Category analysis
            category_stats = {}
            for cat_key, cat_name in BIRTHDAY_CATEGORIES.items():
                count = sum(1 for b in active_birthdays if b['category'] == cat_key)
                percentage = (count / active_birthdays_count * 100) if active_birthdays_count > 0 else 0
                category_stats[cat_name] = {
                    'count': count,
                    'percentage': round(percentage, 1)
                }
            
            # Age analysis
            ages = [b['age'] for b in df_data if not b['is_deleted']]
            age_stats = {
                'average': round(sum(ages) / len(ages), 1) if ages else 0,
                'min': min(ages) if ages else 0,
                'max': max(ages) if ages else 0,
                'median': sorted(ages)[len(ages)//2] if ages else 0
            }
            
            # Monthly distribution
            monthly_distribution = {}
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            for i, month_name in enumerate(month_names, 1):
                count = sum(1 for b in df_data if b['birth_month'] == i and not b['is_deleted'])
                monthly_distribution[month_name] = count
            
            # User engagement analysis
            users_with_images = sum(1 for b in df_data if b['has_image'] and not b['is_deleted'])
            users_with_notes = sum(1 for b in df_data if b['has_notes'] and not b['is_deleted'])
            
            # User activity levels
            user_birthday_counts = {}
            for b in df_data:
                if not b['is_deleted']:
                    user_birthday_counts[b['user_id']] = user_birthday_counts.get(b['user_id'], 0) + 1
            
            if user_birthday_counts:
                avg_birthdays_per_user = round(sum(user_birthday_counts.values()) / len(user_birthday_counts), 1)
                most_active_user_count = max(user_birthday_counts.values())
            else:
                avg_birthdays_per_user = 0
                most_active_user_count = 0
            
            return {
                "overview": {
                    "total_users": total_users,
                    "total_birthdays": total_birthdays,
                    "active_birthdays": active_birthdays_count,
                    "deleted_birthdays": deleted_birthdays_count,
                    "deletion_rate": round(deleted_birthdays_count / total_birthdays * 100, 1) if total_birthdays > 0 else 0
                },
                "category_distribution": category_stats,
                "age_statistics": age_stats,
                "monthly_distribution": monthly_distribution,
                "engagement": {
                    "birthdays_with_images": users_with_images,
                    "birthdays_with_notes": users_with_notes,
                    "image_usage_rate": round(users_with_images / active_birthdays_count * 100, 1) if active_birthdays_count > 0 else 0,
                    "notes_usage_rate": round(users_with_notes / active_birthdays_count * 100, 1) if active_birthdays_count > 0 else 0
                },
                "user_activity": {
                    "average_birthdays_per_user": avg_birthdays_per_user,
                    "most_birthdays_by_single_user": most_active_user_count,
                    "total_active_users": len(user_birthday_counts)
                }
            }
            
        except Exception as e:
            return {"error": f"Error generating analytics: {str(e)}"}
    
    @staticmethod
    async def get_user_count() -> int:
        """Get total number of users"""
        return await User.filter(is_deleted=False).count()
    
    @staticmethod
    async def get_birthday_count() -> int:
        """Get total number of active birthdays"""
        return await Birthday.filter(is_deleted=False).count()
    
    @staticmethod
    async def get_deleted_birthdays_count() -> int:
        """Get total number of deleted birthdays"""
        return await Birthday.filter(is_deleted=True).count()