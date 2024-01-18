from tortoise import fields
from tortoise.models import Model
from datetime import datetime, timezone

class User(Model):
    id=fields.IntField(pk=True)
    name=fields.CharField(max_length=255,null=True)
    phone=fields.CharField(unique=True,null=False,max_length=255)
    email=fields.CharField(max_length=255,unique=True,null=True)
    telegram=fields.CharField(max_length=255,unique=True,null=True)
    birthday=fields.DateField(null=True)
    promocodes=fields.ManyToManyField('models.PromoCodePercent')
    bonuses=fields.IntField(default=0,ge=0)
    code=fields.CharField(max_length=255)
    time_expires=fields.DatetimeField()

    async def get_all_promocodes(self):
        promocodes_set = await self.promocodes.filter(is_active=True)
        promocodes = []
        for i in promocodes_set:
            if(i.end > datetime.now(timezone.utc)):
                promocodes.append({'promocode': i.short_name,
                                   'discription' : i.discription,
                                   'discount': i.discount,
                                   'expires at': i.end.astimezone()})
        return promocodes

class UserJWT(Model):
    user=fields.ForeignKeyField('models.User',pk=True)
    refresh_code=fields.CharField(max_length=255)
    is_active=fields.BooleanField()