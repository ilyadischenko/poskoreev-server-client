from tortoise import fields
from tortoise.models import Model
from datetime import datetime, timezone
from app.promocodes.models import PromoCode

class User(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, null=True)
    birthday = fields.DateField(null=True)
    email = fields.CharField(max_length=255, unique=True, null=True)
    number = fields.CharField(unique=True, null=False, max_length=255)
    code = fields.CharField(max_length=255)
    expires_at = fields.DatetimeField(null=True)
    telegram = fields.CharField(max_length=255, unique=True, null=True)
    promocodes = fields.ManyToManyField('models.PromoCode')
    bonuses = fields.IntField(default=0, ge=0)

    async def get_all_promocodes(self):
        promocodes_set = await self.promocodes.filter(is_active=True)
        promocodes = []
        for i in promocodes_set:
            if i.end_day > datetime.now(timezone.utc) and i.count!=0 and i.start_day < datetime.now(timezone.utc):
                if i.type == 2:
                    effect = str(i.effect) + '%'
                elif i.type == 3:
                    effect = str(i.effect) + 'р'
                promocodes.append({'promocode': i.short_name,
                                   'description': i.description,
                                   'effect': effect,
                                   'expires_at': i.end_day.astimezone().strftime('%d.%m.%Y')})
        return promocodes



class UserJWT(Model):
    user = fields.ForeignKeyField('models.User', pk=True)
    refresh_code = fields.CharField(max_length=255)
    is_active = fields.BooleanField()

class UserBlacklist(Model):
    user_id = fields.IntField()