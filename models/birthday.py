# models/birthday.py
from tortoise.models import Model
from tortoise import fields
from datetime import datetime
from typing import Optional

class User(Model):
    user_id = fields.BigIntField(pk=True)
    username = fields.CharField(max_length=255, null=True)
    first_name = fields.CharField(max_length=255, null=True)
    is_superadmin = fields.BooleanField(default=False)
    timezone = fields.CharField(max_length=50, default='UTC')
    created_at = fields.DatetimeField(auto_now_add=True)
    is_deleted = fields.BooleanField(default=False)
    deleted_at = fields.DatetimeField(null=True)
    
    class Meta:
        table = "users"

class Birthday(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='birthdays')
    name = fields.CharField(max_length=255)
    birthdate = fields.DateField()
    category = fields.CharField(max_length=50, default='other')  # love, family, relative, work, friend, other
    image_url = fields.TextField(null=True)  # URL to birthday person's image
    notes = fields.TextField(null=True)  # Optional notes about the person
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    is_deleted = fields.BooleanField(default=False)
    deleted_at = fields.DatetimeField(null=True)
    
    class Meta:
        table = "birthdays"