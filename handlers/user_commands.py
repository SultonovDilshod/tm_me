# handlers/user_commands.py
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.birthday_service import BirthdayService
from models.birthday import User
from bot_config import BIRTHDAY_CATEGORIES
import calendar
from datetime import date

class BirthdayStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_image = State()
    waiting_for_notes = State()

async def cmd_start(message: Message):
    """Start command handler"""
    # Create or update user
    await User.get_or_create(
        user_id=message.from_user.id,
        defaults={
            'username': message.from_user.username,
            'first_name': message.from_user.first_name
        }
    )
    
    welcome_text = """
🎉 Welcome to Birthday Reminder Bot!

I'll help you keep track of important birthdays with photos, categories, and automatic reminders.

**Available Commands:**
• `/add` - Add a birthday (interactive)
• `/add_birthday Name YYYY-MM-DD [category]` - Quick add
• `/delete_birthday Name` - Delete a birthday
• `/update_birthday Name` - Update birthday details
• `/my_birthdays` - View your birthdays
• `/categories` - View birthdays by category
• `/birthdays_month MM` - Birthdays in specific month
• `/my_stats` - Your detailed statistics
• `/restore_birthday Name` - Restore deleted birthday

**Categories:** Love 💕, Family 👨‍👩‍👧‍👦, Relative 👥, Work 💼, Friend 👫, Other 🌟

**Example:**
`/add_birthday John 1995-09-27 family`

Let's get started! 🎂
    """
    await message.answer(welcome_text)

async def cmd_add_interactive(message: Message, state: FSMContext):
    """Interactive birthday adding"""
    await message.answer(
        "Let's add a birthday! 🎂\n\n"
        "Please send the birthday details in this format:\n"
        "`Name YYYY-MM-DD`\n\n"
        "Example: `John Smith 1995-09-27`"
    )
    await state.set_state(BirthdayStates.waiting_for_category)

async def process_birthday_data(message: Message, state: FSMContext):
    """Process initial birthday data and ask for category"""
    try:
        parts = message.text.strip().split()
        if len(parts) < 2:
            await message.answer("❌ Please use format: `Name YYYY-MM-DD`")
            return
        
        date_str = parts[-1]
        name = ' '.join(parts[:-1])
        
        # Store data in state
        await state.update_data(name=name, date_str=date_str)
        
        # Create category keyboard
        builder = InlineKeyboardBuilder()
        for cat_key, cat_display in BIRTHDAY_CATEGORIES.items():
            builder.add(InlineKeyboardButton(
                text=cat_display,
                callback_data=f"cat_{cat_key}"
            ))
        builder.adjust(2)
        
        await message.answer(
            f"Great! Adding birthday for **{name}** on **{date_str}**\n\n"
            "Please select a category:",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        await message.answer("❌ Invalid format. Please try again with: `Name YYYY-MM-DD`")

async def process_category_selection(callback_query, state: FSMContext):
    """Handle category selection"""
    category = callback_query.data.replace('cat_', '')
    data = await state.get_data()
    
    await state.update_data(category=category)
    
    category_name = BIRTHDAY_CATEGORIES.get(category, category)
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📷 Add Photo", callback_data="add_photo"))
    builder.add(InlineKeyboardButton(text="✅ Skip Photo", callback_data="skip_photo"))
    
    await callback_query.message.edit_text(
        f"**Category:** {category_name}\n\n"
        "Would you like to add a photo?",
        reply_markup=builder.as_markup()
    )

async def process_photo_choice(callback_query, state: FSMContext):
    """Handle photo choice"""
    if callback_query.data == "add_photo":
        await callback_query.message.edit_text(
            "📷 Please send a photo URL or type 'skip' to continue without a photo."
        )
        await state.set_state(BirthdayStates.waiting_for_image)
    else:
        await state.update_data(image_url=None)
        await ask_for_notes(callback_query.message, state)

async def process_image_url(message: Message, state: FSMContext):
    """Process image URL"""
    if message.text.lower() == 'skip':
        await state.update_data(image_url=None)
    else:
        await state.update_data(image_url=message.text.strip())
    
    await ask_for_notes(message, state)

async def ask_for_notes(message: Message, state: FSMContext):
    """Ask for optional notes"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📝 Add Notes", callback_data="add_notes"))
    builder.add(InlineKeyboardButton(text="✅ Skip Notes", callback_data="skip_notes"))
    
    await message.answer(
        "Would you like to add any notes about this person?",
        reply_markup=builder.as_markup()
    )

async def process_notes_choice(callback_query, state: FSMContext):
    """Handle notes choice"""
    if callback_query.data == "add_notes":
        await callback_query.message.edit_text(
            "📝 Please write your notes or type 'skip' to continue without notes."
        )
        await state.set_state(BirthdayStates.waiting_for_notes)
    else:
        await state.update_data(notes=None)
        await finalize_birthday_creation(callback_query.message, state)

async def process_notes(message: Message, state: FSMContext):
    """Process notes"""
    if message.text.lower() == 'skip':
        await state.update_data(notes=None)
    else:
        await state.update_data(notes=message.text.strip())
    
    await finalize_birthday_creation(message, state)

async def finalize_birthday_creation(message: Message, state: FSMContext):
    """Create the birthday with all collected data"""
    data = await state.get_data()
    
    result = await BirthdayService.add_birthday(
        user_id=message.from_user.id,
        name=data['name'],
        birthdate_str=data['date_str'],
        category=data.get('category', 'other'),
        image_url=data.get('image_url'),
        notes=data.get('notes')
    )
    
    if result["success"]:
        response = f"✅ {result['message']}"
        
        if data.get('image_url'):
            response += f"\n📷 Photo: {data['image_url']}"
        if data.get('notes'):
            response += f"\n📝 Notes: {data['notes']}"
            
        await message.answer(response)
    else:
        await message.answer(f"❌ {result['message']}")
    
    await state.clear()

async def cmd_add_birthday(message: Message):
    """Quick add birthday command handler"""
    try:
        # Parse command arguments
        args = message.text.split()[1:]  # Remove command part
        if len(args) < 2:
            await message.answer(
                "❌ Invalid format!\n\n"
                "Use: `/add_birthday Name YYYY-MM-DD [category]`\n"
                "Example: `/add_birthday John 1995-09-27 family`\n\n"
                f"Available categories: {', '.join(BIRTHDAY_CATEGORIES.keys())}"
            )
            return
        
        # Parse arguments
        if len(args) >= 3 and args[-1].lower() in BIRTHDAY_CATEGORIES:
            # Category provided
            category = args[-1].lower()
            date_str = args[-2]
            name = ' '.join(args[:-2])
        else:
            # No category provided
            category = 'other'
            date_str = args[-1]
            name = ' '.join(args[:-1])
        
        result = await BirthdayService.add_birthday(
            message.from_user.id, name, date_str, category
        )
        
        if result["success"]:
            await message.answer(f"✅ {result['message']}")
        else:
            await message.answer(f"❌ {result['message']}")
            
    except Exception as e:
        await message.answer("❌ An error occurred. Please try again.")

async def cmd_delete_birthday(message: Message):
    """Delete birthday command handler"""
    try:
        args = message.text.split()[1:]
        if not args:
            await message.answer(
                "❌ Please specify a name!\n\n"
                "Use: `/delete_birthday Name`\n"
                "Example: `/delete_birthday John`"
            )
            return
        
        name = ' '.join(args)
        result = await BirthdayService.delete_birthday(message.from_user.id, name)
        
        if result["success"]:
            await message.answer(f"✅ {result['message']}")
        else:
            await message.answer(f"❌ {result['message']}")
            
    except Exception as e:
        await message.answer("❌ An error occurred. Please try again.")

async def cmd_update_birthday(message: Message):
    """Update birthday command handler"""
    try:
        args = message.text.split()[1:]
        if not args:
            await message.answer(
                "❌ Please specify a name!\n\n"
                "Use: `/update_birthday Name`\n"
                "Then I'll guide you through the update process."
            )
            return
        
        name = ' '.join(args)
        
        # Check if birthday exists
        birthdays = await BirthdayService.get_user_birthdays(message.from_user.id)
        birthday = next((b for b in birthdays if b.name.lower() == name.lower()), None)
        
        if not birthday:
            await message.answer(f"❌ Birthday for {name} not found")
            return
        
        # Create update options keyboard
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="📅 Date", callback_data=f"update_date_{birthday.id}"))
        builder.add(InlineKeyboardButton(text="🏷️ Category", callback_data=f"update_category_{birthday.id}"))
        builder.add(InlineKeyboardButton(text="📷 Photo", callback_data=f"update_photo_{birthday.id}"))
        builder.add(InlineKeyboardButton(text="📝 Notes", callback_data=f"update_notes_{birthday.id}"))
        builder.adjust(2)
        
        category_display = BIRTHDAY_CATEGORIES.get(birthday.category, birthday.category)
        
        text = f"**{birthday.name}**\n"
        text += f"📅 Date: {birthday.birthdate.strftime('%Y-%m-%d')}\n"
        text += f"🏷️ Category: {category_display}\n"
        text += f"📷 Photo: {'Yes' if birthday.image_url else 'No'}\n"
        text += f"📝 Notes: {'Yes' if birthday.notes else 'No'}\n\n"
        text += "What would you like to update?"
        
        await message.answer(text, reply_markup=builder.as_markup())
            
    except Exception as e:
        await message.answer("❌ An error occurred. Please try again.")

async def cmd_my_birthdays(message: Message):
    """List user's birthdays with enhanced display"""
    try:
        birthdays = await BirthdayService.get_user_birthdays(message.from_user.id)
        
        if not birthdays:
            await message.answer(
                "📝 You haven't added any birthdays yet!\n\n"
                "Use `/add` for interactive adding or `/add_birthday Name YYYY-MM-DD` for quick add."
            )
            return
        
        text = "🎂 **Your Birthdays:**\n\n"
        
        # Group by category
        categories = {}
        for birthday in birthdays:
            cat = birthday.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(birthday)
        
        for cat_key, birthday_list in categories.items():
            cat_display = BIRTHDAY_CATEGORIES.get(cat_key, cat_key)
            text += f"**{cat_display}**\n"
            
            for birthday in birthday_list:
                age = date.today().year - birthday.birthdate.year
                text += f"• **{birthday.name}** - {birthday.birthdate.strftime('%B %d, %Y')} (Age: {age})"
                if birthday.image_url:
                    text += " 📷"
                if birthday.notes:
                    text += " 📝"
                text += "\n"
            text += "\n"
        
        # Truncate if too long
        if len(text) > 4000:
            text = text[:3900] + "...\n\nToo many birthdays to display all at once!"
        
        await message.answer(text)
        
    except Exception as e:
        await message.answer("❌ An error occurred. Please try again.")

async def cmd_categories(message: Message):
    """Show categories with selection"""
    builder = InlineKeyboardBuilder()
    for cat_key, cat_display in BIRTHDAY_CATEGORIES.items():
        builder.add(InlineKeyboardButton(
            text=cat_display,
            callback_data=f"view_cat_{cat_key}"
        ))
    builder.adjust(2)
    
    await message.answer(
        "🏷️ **Birthday Categories**\n\n"
        "Select a category to view birthdays:",
        reply_markup=builder.as_markup()
    )

async def show_category_birthdays(callback_query):
    """Show birthdays for selected category"""
    category = callback_query.data.replace('view_cat_', '')
    birthdays = await BirthdayService.get_birthdays_by_category(
        callback_query.from_user.id, 
        category
    )
    
    category_display = BIRTHDAY_CATEGORIES.get(category, category)
    
    if not birthdays:
        await callback_query.message.edit_text(
            f"📝 No birthdays found in category: {category_display}"
        )
        return
    
    text = f"🏷️ **{category_display} Birthdays:**\n\n"
    
    for birthday in birthdays:
        age = date.today().year - birthday.birthdate.year
        text += f"• **{birthday.name}** - {birthday.birthdate.strftime('%B %d, %Y')} (Age: {age})"
        if birthday.image_url:
            text += " 📷"
        if birthday.notes:
            text += " 📝"
        text += "\n"
    
    await callback_query.message.edit_text(text)

async def cmd_restore_birthday(message: Message):
    """Restore deleted birthday"""
    try:
        args = message.text.split()[1:]
        if not args:
            await message.answer(
                "❌ Please specify a name!\n\n"
                "Use: `/restore_birthday Name`\n"
                "Example: `/restore_birthday John`"
            )
            return
        
        name = ' '.join(args)
        result = await BirthdayService.restore_deleted_birthday(message.from_user.id, name)
        
        if result["success"]:
            await message.answer(f"✅ {result['message']}")
        else:
            await message.answer(f"❌ {result['message']}")
            
    except Exception as e:
        await message.answer("❌ An error occurred. Please try again.")

async def cmd_birthdays_month(message: Message):
    """List birthdays for specific month"""
    try:
        args = message.text.split()[1:]
        if not args:
            await message.answer(
                "❌ Please specify a month!\n\n"
                "Use: `/birthdays_month MM`\n"
                "Example: `/birthdays_month 09` for September"
            )
            return
        
        try:
            month = int(args[0])
        except ValueError:
            await message.answer("❌ Invalid month format. Use numbers 01-12.")
            return
        
        if month < 1 or month > 12:
            await message.answer("❌ Month must be between 01 and 12.")
            return
        
        birthdays = await BirthdayService.get_birthdays_by_month(
            message.from_user.id, month
        )
        
        if not birthdays:
            month_name = calendar.month_name[month]
            await message.answer(f"📅 No birthdays in {month_name}.")
            return
        
        month_name = calendar.month_name[month]
        text = f"🗓️ **Birthdays in {month_name}:**\n\n"
        
        for birthday in birthdays:
            age = date.today().year - birthday.birthdate.year
            category_display = BIRTHDAY_CATEGORIES.get(birthday.category, birthday.category)
            text += f"• **{birthday.name}** - {birthday.birthdate.strftime('%B %d, %Y')} (Age: {age})\n"
            text += f"  🏷️ {category_display}"
            if birthday.image_url:
                text += " 📷"
            if birthday.notes:
                text += " 📝"
            text += "\n\n"
        
        await message.answer(text)
        
    except Exception as e:
        await message.answer("❌ An error occurred. Please try again.")

async def cmd_my_stats(message: Message):
    """Show enhanced user statistics"""
    try:
        stats = await BirthdayService.get_user_stats(message.from_user.id)
        
        if not stats or stats['total_birthdays'] == 0:
            await message.answer("📊 No statistics available. Add some birthdays first!")
            return
        
        text = "📊 **Your Birthday Statistics:**\n\n"
        
        # Overview
        text += f"📈 **Overview:**\n"
        text += f"• Total birthdays: {stats['total_birthdays']}\n"
        text += f"• Upcoming this month: {stats['upcoming_this_month']}\n"
        text += f"• Average age: {stats['average_age']} years\n"
        text += f"• Age range: {stats['age_range']['min']}-{stats['age_range']['max']} years\n\n"
        
        # Next birthday
        if stats['next_birthday']:
            next_bd = stats['next_birthday']
            category_display = BIRTHDAY_CATEGORIES.get(next_bd['category'], next_bd['category'])
            text += f"🎯 **Next Birthday:**\n"
            text += f"**{next_bd['name']}** in {next_bd['days_until']} days "
            text += f"({next_bd['date'].strftime('%B %d')}) - {category_display}\n\n"
        
        # Categories
        if stats['category_breakdown']:
            text += f"🏷️ **Categories:**\n"
            for category, count in stats['category_breakdown'].items():
                category_display = BIRTHDAY_CATEGORIES.get(category, category)
                percentage = round(count / stats['total_birthdays'] * 100, 1)
                text += f"• {category_display}: {count} ({percentage}%)\n"
            text += "\n"
        
        # Monthly distribution (top months)
        if stats['monthly_distribution']:
            text += f"📅 **Top Birth Months:**\n"
            sorted_months = sorted(
                stats['monthly_distribution'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]  # Top 3 months
            
            for month, count in sorted_months:
                if count > 0:
                    text += f"• {month}: {count}\n"
        
        await message.answer(text)
        
    except Exception as e:
        await message.answer("❌ An error occurred. Please try again.")

async def cmd_set_timezone(message: Message):
    """Set user timezone (placeholder for future implementation)"""
    await message.answer(
        "🕒 **Timezone Setting**\n\n"
        "This feature is coming soon! Currently using UTC timezone.\n"
        "Future: `/set_timezone America/New_York`"
    )

# Callback handlers
async def handle_category_callback(callback_query, state: FSMContext):
    """Handle category selection callbacks"""
    if callback_query.data.startswith('cat_'):
        await process_category_selection(callback_query, state)
    elif callback_query.data in ['add_photo', 'skip_photo']:
        await process_photo_choice(callback_query, state)
    elif callback_query.data in ['add_notes', 'skip_notes']:
        await process_notes_choice(callback_query, state)
    elif callback_query.data.startswith('view_cat_'):
        await show_category_birthdays(callback_query)
    elif callback_query.data.startswith('update_'):
        await handle_update_callback(callback_query)

async def handle_update_callback(callback_query):
    """Handle update callbacks"""
    parts = callback_query.data.split('_')
    action = parts[1]  # date, category, photo, notes
    birthday_id = int(parts[2])
    
    if action == 'date':
        await callback_query.message.edit_text(
            "📅 Please send the new date in format YYYY-MM-DD:"
        )
    elif action == 'category':
        builder = InlineKeyboardBuilder()
        for cat_key, cat_display in BIRTHDAY_CATEGORIES.items():
            builder.add(InlineKeyboardButton(
                text=cat_display,
                callback_data=f"setcat_{cat_key}_{birthday_id}"
            ))
        builder.adjust(2)
        
        await callback_query.message.edit_text(
            "🏷️ Select new category:",
            reply_markup=builder.as_markup()
        )
    elif action == 'photo':
        await callback_query.message.edit_text(
            "📷 Please send the new photo URL or 'remove' to delete current photo:"
        )
    elif action == 'notes':
        await callback_query.message.edit_text(
            "📝 Please send the new notes or 'remove' to delete current notes:"
        )

def register_user_handlers(dp: Dispatcher):
    """Register all user command handlers"""
    dp.message.register(cmd_start, Command('start'))
    dp.message.register(cmd_add_interactive, Command('add'))
    dp.message.register(cmd_add_birthday, Command('add_birthday'))
    dp.message.register(cmd_delete_birthday, Command('delete_birthday'))
    dp.message.register(cmd_update_birthday, Command('update_birthday'))
    dp.message.register(cmd_restore_birthday, Command('restore_birthday'))
    dp.message.register(cmd_my_birthdays, Command('my_birthdays'))
    dp.message.register(cmd_categories, Command('categories'))
    dp.message.register(cmd_birthdays_month, Command('birthdays_month'))
    dp.message.register(cmd_my_stats, Command('my_stats'))
    dp.message.register(cmd_set_timezone, Command('set_timezone'))
    
    # State handlers
    dp.message.register(process_birthday_data, BirthdayStates.waiting_for_category)
    dp.message.register(process_image_url, BirthdayStates.waiting_for_image)
    dp.message.register(process_notes, BirthdayStates.waiting_for_notes)
    
    # Callback handlers
    dp.callback_query.register(handle_category_callback)