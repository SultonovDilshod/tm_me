# handlers/admin_commands.py
from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot_config import SUPERADMIN_ID, BIRTHDAY_CATEGORIES
from services.admin_service import AdminService
from services.birthday_service import BirthdayService
from models.birthday import User
import io

async def is_superadmin(message: Message) -> bool:
    """Check if user is superadmin"""
    return message.from_user.id == SUPERADMIN_ID

async def cmd_all_birthdays(message: Message):
    """Admin command to view all birthdays"""
    if not await is_superadmin(message):
        await message.answer("❌ Access denied. Admin only.")
        return
    
    try:
        # Create options keyboard
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="📊 Active Only", callback_data="admin_birthdays_active"))
        builder.add(InlineKeyboardButton(text="🗑️ Include Deleted", callback_data="admin_birthdays_all"))
        
        await message.answer(
            "👑 **Admin: View Birthdays**\n\n"
            "Choose what to display:",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)}")

async def show_admin_birthdays(callback_query, include_deleted: bool = False):
    """Show birthdays for admin"""
    try:
        birthdays = await AdminService.get_all_birthdays(include_deleted)
        
        if not birthdays:
            text = "📝 No birthdays found in the database."
            await callback_query.message.edit_text(text)
            return
        
        status_text = "All Birthdays" if include_deleted else "Active Birthdays"
        text = f"👑 **{status_text} (Admin View):**\n\n"
        
        # Group by status if including deleted
        if include_deleted:
            active = [b for b in birthdays if not b['is_deleted']]
            deleted = [b for b in birthdays if b['is_deleted']]
            
            text += f"✅ **Active ({len(active)}):**\n"
            for birthday in active[:10]:  # Limit display
                category_display = BIRTHDAY_CATEGORIES.get(birthday['category'], birthday['category'])
                text += (f"• **{birthday['name']}** ({birthday['birthdate'].strftime('%Y-%m-%d')}) "
                        f"- User: {birthday['user_id']} - {category_display}")
                if birthday['image_url']:
                    text += " 📷"
                text += "\n"
            
            if len(active) > 10:
                text += f"... and {len(active) - 10} more active birthdays\n"
            
            text += f"\n🗑️ **Deleted ({len(deleted)}):**\n"
            for birthday in deleted[:5]:  # Limit deleted display
                category_display = BIRTHDAY_CATEGORIES.get(birthday['category'], birthday['category'])
                text += (f"• **{birthday['name']}** ({birthday['birthdate'].strftime('%Y-%m-%d')}) "
                        f"- User: {birthday['user_id']} - {category_display}\n")
            
            if len(deleted) > 5:
                text += f"... and {len(deleted) - 5} more deleted birthdays\n"
        else:
            for birthday in birthdays[:20]:  # Limit to first 20
                category_display = BIRTHDAY_CATEGORIES.get(birthday['category'], birthday['category'])
                text += (f"• **{birthday['name']}** ({birthday['birthdate'].strftime('%Y-%m-%d')}) "
                        f"- User: {birthday['user_id']} - {category_display}")
                if birthday['image_url']:
                    text += " 📷"
                if birthday['notes']:
                    text += " 📝"
                text += "\n"
            
            if len(birthdays) > 20:
                text += f"\n... and {len(birthdays) - 20} more entries."
        
        text += f"\n\n**Total: {len(birthdays)} birthdays**"
        
        await callback_query.message.edit_text(text)
        
    except Exception as e:
        await callback_query.message.edit_text(f"❌ Error retrieving birthdays: {str(e)}")

async def cmd_user_stats(message: Message):
    """Admin command to view specific user stats"""
    if not await is_superadmin(message):
        await message.answer("❌ Access denied. Admin only.")
        return
    
    try:
        args = message.text.split()[1:]
        if not args:
            await message.answer(
                "❌ Please specify a user ID!\n\n"
                "Use: `/user_stats <user_id>`"
            )
            return
        
        try:
            user_id = int(args[0])
        except ValueError:
            await message.answer("❌ Invalid user ID format.")
            return
        
        # Check if user exists
        user = await User.get_or_none(user_id=user_id)
        if not user:
            await message.answer(f"❌ User {user_id} not found.")
            return
        
        stats = await BirthdayService.get_user_stats(user_id)
        
        text = f"📊 **Admin: Stats for User {user_id}:**\n"
        text += f"Username: {user.username or 'N/A'}\n"
        text += f"Name: {user.first_name or 'N/A'}\n"
        text += f"Timezone: {user.timezone}\n"
        text += f"Created: {user.created_at.strftime('%Y-%m-%d')}\n\n"
        
        if stats and stats['total_birthdays'] > 0:
            text += f"📈 **Birthday Statistics:**\n"
            text += f"• Total birthdays: {stats['total_birthdays']}\n"
            text += f"• Average age: {stats['average_age']} years\n"
            text += f"• Upcoming this month: {stats['upcoming_this_month']}\n\n"
            
            # Categories
            if stats['category_breakdown']:
                text += f"🏷️ **Categories:**\n"
                for category, count in stats['category_breakdown'].items():
                    category_display = BIRTHDAY_CATEGORIES.get(category, category)
                    text += f"• {category_display}: {count}\n"
                text += "\n"
            
            if stats['next_birthday']:
                next_bd = stats['next_birthday']
                category_display = BIRTHDAY_CATEGORIES.get(next_bd['category'], next_bd['category'])
                text += f"🎯 **Next birthday:** {next_bd['name']} in {next_bd['days_until']} days ({category_display})"
        else:
            text += "📝 No birthdays found for this user."
        
        await message.answer(text)
        
    except Exception as e:
        await message.answer(f"❌ Error retrieving user stats: {str(e)}")

async def cmd_export_csv(message: Message):
    """Admin command to export all data to CSV"""
    if not await is_superadmin(message):
        await message.answer("❌ Access denied. Admin only.")
        return
    
    try:
        # Create options keyboard
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="📊 Active Only", callback_data="export_active"))
        builder.add(InlineKeyboardButton(text="🗂️ All Data", callback_data="export_all"))
        
        await message.answer(
            "📊 **CSV Export Options:**\n\n"
            "Choose what to export:",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)}")

async def handle_export_callback(callback_query):
    """Handle CSV export callbacks"""
    try:
        include_deleted = callback_query.data == "export_all"
        
        await callback_query.message.edit_text("📊 Generating CSV export...")
        
        csv_data = await AdminService.export_to_csv(include_deleted)
        csv_content = csv_data.getvalue()
        
        if not csv_content.strip():
            await callback_query.message.edit_text("📝 No data to export.")
            return
        
        # Create filename
        status = "complete" if include_deleted else "active"
        filename = f"birthdays_export_{status}_{callback_query.message.date.strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Create file
        file_bytes = csv_content.encode('utf-8')
        input_file = BufferedInputFile(file_bytes, filename=filename)
        
        await callback_query.message.answer_document(
            input_file,
            caption=f"📊 Birthday database export ({status} data)"
        )
        
    except Exception as e:
        await callback_query.message.edit_text(f"❌ Error exporting data: {str(e)}")

async def cmd_analytics(message: Message):
    """Admin command to view comprehensive analytics"""
    if not await is_superadmin(message):
        await message.answer("❌ Access denied. Admin only.")
        return
    
    try:
        await message.answer("📊 Generating analytics report...")
        
        analytics = await AdminService.get_analytics_report()
        
        if "error" in analytics:
            await message.answer(f"❌ {analytics['error']}")
            return
        
        text = "📊 **Comprehensive Analytics Report**\n\n"
        
        # Overview
        overview = analytics["overview"]
        text += f"📈 **Overview:**\n"
        text += f"• Total Users: {overview['total_users']}\n"
        text += f"• Total Birthdays: {overview['total_birthdays']}\n"
        text += f"• Active Birthdays: {overview['active_birthdays']}\n"
        text += f"• Deleted Birthdays: {overview['deleted_birthdays']}\n"
        text += f"• Deletion Rate: {overview['deletion_rate']}%\n\n"
        
        # User Activity
        activity = analytics["user_activity"]
        text += f"👥 **User Activity:**\n"
        text += f"• Active Users: {activity['total_active_users']}\n"
        text += f"• Avg Birthdays/User: {activity['average_birthdays_per_user']}\n"
        text += f"• Most by Single User: {activity['most_birthdays_by_single_user']}\n\n"
        
        # Category Distribution
        text += f"🏷️ **Category Distribution:**\n"
        for category, stats in analytics["category_distribution"].items():
            text += f"• {category}: {stats['count']} ({stats['percentage']}%)\n"
        text += "\n"
        
        # Engagement
        engagement = analytics["engagement"]
        text += f"💡 **Engagement:**\n"
        text += f"• Photos Added: {engagement['birthdays_with_images']} ({engagement['image_usage_rate']}%)\n"
        text += f"• Notes Added: {engagement['birthdays_with_notes']} ({engagement['notes_usage_rate']}%)\n\n"
        
        # Age Statistics
        age_stats = analytics["age_statistics"]
        text += f"🎂 **Age Analysis:**\n"
        text += f"• Average Age: {age_stats['average']} years\n"
        text += f"• Age Range: {age_stats['min']}-{age_stats['max']} years\n"
        text += f"• Median Age: {age_stats['median']} years\n"
        
        await message.answer(text)
        
    except Exception as e:
        await message.answer(f"❌ Error generating analytics: {str(e)}")

async def cmd_broadcast(message: Message):
    """Admin command to broadcast message to all users"""
    if not await is_superadmin(message):
        await message.answer("❌ Access denied. Admin only.")
        return
    
    try:
        args = message.text.split(maxsplit=1)[1:]
        if not args:
            await message.answer(
                "❌ Please specify a message!\n\n"
                "Use: `/broadcast Your message here`"
            )
            return
        
        broadcast_message = args[0]
        users = await User.filter(is_deleted=False)
        
        success_count = 0
        failed_count = 0
        
        await message.answer(f"📢 Starting broadcast to {len(users)} users...")
        
        for user in users:
            try:
                await message.bot.send_message(
                    user.user_id,
                    f"📢 **Broadcast Message:**\n\n{broadcast_message}"
                )
                success_count += 1
            except Exception:
                failed_count += 1
        
        await message.answer(
            f"📢 **Broadcast Complete:**\n"
            f"✅ Successful: {success_count}\n"
            f"❌ Failed: {failed_count}"
        )
        
    except Exception as e:
        await message.answer(f"❌ Error broadcasting: {str(e)}")

async def cmd_admin_stats(message: Message):
    """Admin command to view global statistics"""
    if not await is_superadmin(message):
        await message.answer("❌ Access denied. Admin only.")
        return
    
    try:
        user_count = await AdminService.get_user_count()
        birthday_count = await AdminService.get_birthday_count()
        deleted_count = await AdminService.get_deleted_birthdays_count()
        
        text = "👑 **Admin Dashboard:**\n\n"
        text += f"📊 **Quick Stats:**\n"
        text += f"• Total Users: {user_count}\n"
        text += f"• Active Birthdays: {birthday_count}\n"
        text += f"• Deleted Birthdays: {deleted_count}\n"
        text += f"• Total Database Entries: {birthday_count + deleted_count}\n"
        
        if user_count > 0:
            avg_per_user = round(birthday_count / user_count, 1)
            text += f"• Average per User: {avg_per_user}\n"
        
        if birthday_count + deleted_count > 0:
            deletion_rate = round(deleted_count / (birthday_count + deleted_count) * 100, 1)
            text += f"• Deletion Rate: {deletion_rate}%\n"
        
        text += f"\n**Available Commands:**\n"
        text += f"• `/all_birthdays` - View all birthdays\n"
        text += f"• `/analytics` - Detailed analytics\n"
        text += f"• `/export_csv` - Export data\n"
        text += f"• `/user_stats <id>` - User details\n"
        text += f"• `/broadcast <msg>` - Send message to all\n"
        
        await message.answer(text)
        
    except Exception as e:
        await message.answer(f"❌ Error retrieving admin stats: {str(e)}")

async def handle_admin_callbacks(callback_query):
    """Handle admin callback queries"""
    if callback_query.data == "admin_birthdays_active":
        await show_admin_birthdays(callback_query, include_deleted=False)
    elif callback_query.data == "admin_birthdays_all":
        await show_admin_birthdays(callback_query, include_deleted=True)
    elif callback_query.data in ["export_active", "export_all"]:
        await handle_export_callback(callback_query)

def register_admin_handlers(dp: Dispatcher):
    """Register all admin command handlers"""
    dp.message.register(cmd_all_birthdays, Command('all_birthdays'))
    dp.message.register(cmd_user_stats, Command('user_stats'))
    dp.message.register(cmd_export_csv, Command('export_csv'))
    dp.message.register(cmd_analytics, Command('analytics'))
    dp.message.register(cmd_broadcast, Command('broadcast'))
    dp.message.register(cmd_admin_stats, Command('admin_stats'))
    
    # Admin callback handlers
    dp.callback_query.register(handle_admin_callbacks)