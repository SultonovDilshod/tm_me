# database/init_db.py
from tortoise import Tortoise
from bot_config import DATABASE_URL, SUPERADMIN_ID
from models.birthday import User

TORTOISE_ORM = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": ["models.birthday"],
            "default_connection": "default",
        },
    },
}

async def init_database():
    """Initialize database and create tables"""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    
    # Create superadmin user if not exists
    superadmin, created = await User.get_or_create(
        user_id=SUPERADMIN_ID,
        defaults={'is_superadmin': True}
    )
    if created:
        print(f"Superadmin user created with ID: {SUPERADMIN_ID}")
