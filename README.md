\# 🎂 Enhanced Birthday Reminder Telegram Bot



An advanced Telegram bot for managing birthdays with photos, categories, automatic reminders, and comprehensive analytics, built with Python, aiogram v3, and SQLite.



\## ✨ Enhanced Features



\### 🖼️ \*\*Image Support\*\*

\- Add photos for each birthday person via URL

\- Images stored as URLs in the database

\- Photo validation and display in reminders

\- Visual birthday cards in notifications



\### 🏷️ \*\*Categories\*\*

\- \*\*Love\*\* 💕 - Your romantic partner

\- \*\*Family\*\* 👨‍👩‍👧‍👦 - Family members  

\- \*\*Relative\*\* 👥 - Extended family

\- \*\*Work\*\* 💼 - Colleagues and professional contacts

\- \*\*Friend\*\* 👫 - Friends and social contacts

\- \*\*Other\*\* 🌟 - Everyone else



\### 🗑️ \*\*Soft Delete System\*\*

\- Birthdays are never permanently deleted

\- Deleted items kept with `deleted` status

\- Ability to restore deleted birthdays

\- Complete audit trail for admin analysis



\### 📊 \*\*Advanced Analytics\*\*

\- Comprehensive pandas-powered data analysis

\- Category distribution and trends

\- Age statistics and demographics

\- User engagement metrics

\- Monthly birthday patterns

\- Export capabilities for detailed analysis



\## 🚀 User Features



\### \*\*Basic Commands\*\*

\- `/start` - Welcome message and help

\- `/add` - Interactive birthday creation

\- `/add\_birthday Name YYYY-MM-DD \[category]` - Quick add

\- `/delete\_birthday Name` - Delete a birthday (soft delete)

\- `/restore\_birthday Name` - Restore deleted birthday

\- `/update\_birthday Name` - Update birthday details

\- `/my\_birthdays` - View your birthdays grouped by category

\- `/categories` - Browse birthdays by category

\- `/birthdays\_month MM` - View birthdays in specific month

\- `/my\_stats` - Detailed personal statistics



\### \*\*Interactive Features\*\*

\- Step-by-step birthday creation with category selection

\- Photo URL addition with validation

\- Optional notes for each birthday

\- Visual category browsing with emoji indicators

\- Enhanced birthday displays with photos and notes



\## 👑 Admin Features



\### \*\*Data Management\*\*

\- `/all\_birthdays` - View all user data (active/deleted)

\- `/user\_stats <user\_id>` - Detailed user statistics

\- `/export\_csv` - Export data to CSV (active or all data)

\- `/analytics` - Comprehensive analytics report

\- `/broadcast <message>` - Send message to all users

\- `/admin\_stats` - Quick admin dashboard



\### \*\*Advanced Analytics\*\*

\- User engagement statistics

\- Category distribution analysis

\- Age demographics and trends

\- Photo/notes usage rates

\- Monthly birthday patterns

\- User activity levels



\## 🗃️ Database Schema (SQLite)



\### \*\*Users Table\*\*

```sql

CREATE TABLE users (

&nbsp;   user\_id INTEGER PRIMARY KEY,

&nbsp;   username VARCHAR(255),

&nbsp;   first\_name VARCHAR(255),

&nbsp;   is\_superadmin BOOLEAN DEFAULT FALSE,

&nbsp;   timezone VARCHAR(50) DEFAULT 'UTC',

&nbsp;   created\_at DATETIME DEFAULT CURRENT\_TIMESTAMP,

&nbsp;   is\_deleted BOOLEAN DEFAULT FALSE,

&nbsp;   deleted\_at DATETIME NULL

);

```



\### \*\*Birthdays Table\*\*

```sql

CREATE TABLE birthdays (

&nbsp;   id INTEGER PRIMARY KEY AUTOINCREMENT,

&nbsp;   user\_id INTEGER REFERENCES users(user\_id),

&nbsp;   name VARCHAR(255) NOT NULL,

&nbsp;   birthdate DATE NOT NULL,

&nbsp;   category VARCHAR(50) DEFAULT 'other',

&nbsp;   image\_url TEXT NULL,

&nbsp;   notes TEXT NULL,

&nbsp;   created\_at DATETIME DEFAULT CURRENT\_TIMESTAMP,

&nbsp;   updated\_at DATETIME DEFAULT CURRENT\_TIMESTAMP,

&nbsp;   is\_deleted BOOLEAN DEFAULT FALSE,

&nbsp;   deleted\_at DATETIME NULL

);

```



\## 🚀 Quick Start



\### \*\*Prerequisites\*\*

\- Python 3.11+

\- Telegram Bot Token (from @BotFather)

\- Your Telegram User ID (from @userinfobot)



\### \*\*Installation\*\*



1\. \*\*Download and setup\*\*

```bash

git clone <repository-url>

cd birthday\_bot

pip install -r requirements.txt

```



2\. \*\*Configure environment\*\*

```bash

cp .env.example .env

\# Edit .env with your details:

\# BOT\_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyZ

\# SUPERADMIN\_ID=123456789

```



3\. \*\*Run the bot\*\*

```bash

python main.py

```



The SQLite database is created automatically on first run!



\### \*\*Docker Deployment\*\*

```bash

\# Create .env file with your tokens

cp .env.example .env

\# Edit .env with your bot token and admin ID



\# Run with Docker Compose

docker-compose up -d



\# View logs

docker-compose logs -f bot

```



\## 📱 User Experience



\### \*\*Interactive Birthday Creation\*\*

1\. Send `/add` to start interactive mode

2\. Enter `Name YYYY-MM-DD` format

3\. Select category from visual buttons

4\. Optionally add photo URL

5\. Optionally add personal notes

6\. Confirm and save



\### \*\*Smart Reminders\*\*

\- \*\*Daily reminders\*\* at 9 AM with photos and category info

\- \*\*Weekly upcoming alerts\*\* every Sunday at 8 AM

\- \*\*Rich notifications\*\* with all stored details

\- \*\*Photo integration\*\* in birthday messages



\### \*\*Category Management\*\*

\- Visual browsing by category with emoji indicators

\- Category statistics in user stats

\- Easy category updates through interactive menus

\- Color-coded displays for better organization



\## 🔧 Technical Features



\### \*\*SQLite Benefits\*\*

\- ✅ \*\*No setup required\*\* - just run the bot

\- ✅ \*\*Easy backup\*\* - copy the .db file

\- ✅ \*\*Portable\*\* - works on any system

\- ✅ \*\*Fast\*\* - perfect for small to medium datasets

\- ✅ \*\*Reliable\*\* - ACID compliant database



\### \*\*Enhanced Validation\*\*

\- URL validation for image links

\- Category validation with predefined options

\- Date validation with reasonable year ranges

\- Input sanitization for security



\### \*\*Soft Delete Benefits\*\*

\- Complete data preservation

\- Easy mistake recovery

\- Full audit trails for analytics

\- No permanent data loss



\## 📊 Analytics Features



\### \*\*User Insights\*\*

\- Total birthdays and upcoming count

\- Category distribution with percentages

\- Age statistics (average, min, max, median)

\- Monthly birthday patterns

\- Photo and notes usage rates



\### \*\*Admin Analytics\*\*

\- User engagement metrics

\- System-wide statistics

\- Category popularity analysis

\- Age demographics across all users

\- Deletion rate monitoring



\## 🔒 Security \& Privacy



\### \*\*Data Protection\*\*

\- Per-user data isolation

\- Admin-only access controls

\- Secure environment variable management

\- Input validation and sanitization



\### \*\*Audit Trail\*\*

\- Soft delete preserves all data

\- Complete history of changes

\- User activity tracking

\- Admin action logging



\## 🎯 Use Cases



\### \*\*Personal Use\*\*

\- Family birthday tracking with photos

\- Friend management with categories

\- Important relationship reminders

\- Visual birthday calendars



\### \*\*Small Business\*\*

\- Employee birthday celebrations

\- Client relationship management

\- Team building and engagement

\- HR analytics and reporting



\## 🚀 Deployment Options



\### \*\*Simple Local\*\*

```bash

python main.py

```



\### \*\*Docker (Recommended)\*\*

```bash

docker-compose up -d

```



\### \*\*VPS/Cloud\*\*

\- Copy files to server

\- Set environment variables

\- Run with systemd or supervisor

\- SQLite file stored locally



\## 🔄 Maintenance



\### \*\*Backup\*\*

```bash

\# Backup SQLite database

cp birthday\_bot.db backup\_$(date +%Y%m%d).db

```



\### \*\*Updates\*\*

```bash

git pull origin main

docker-compose restart bot

```



\### \*\*Monitoring\*\*

\- Check logs: `docker-compose logs bot`

\- Monitor database size

\- Review user activity in admin panel



This enhanced birthday bot provides a complete solution for birthday management with rich features, comprehensive analytics, and a user-friendly experience while maintaining simplicity in deployment and maintenance!

