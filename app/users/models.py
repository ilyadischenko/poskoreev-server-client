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
    expires_at = fields.DatetimeField()
    telegram = fields.CharField(max_length=255, unique=True, null=True)
    promocodes = fields.ManyToManyField('models.PromoCode')
    bonuses = fields.IntField(default=0, ge=0)
    # async def get_promocode(self, promocode : str):
    #     p_id=await PromoCode.get_or_none(short_name=promocode)
    #     if not p_id: return None
    #     p = await self.promocodes.filter(promocode_id=p_id).first()
    #     if not p: return None
    #     return p.short_name
    async def get_all_promocodes(self):
        promocodes_set = await self.promocodes.filter(is_active=True)
        promocodes = []
        for i in promocodes_set:
            if i.end_day > datetime.now(timezone.utc) and i.count!=0:
                promocodes.append({'promocode': i.short_name,
                                   'description': i.description,
                                   #'works_with': await i.get_product_categories(),
                                   'effect': i.effect,
                                   'minimal_sum': i.min_sum,
                                   'expires_at': i.end_day.astimezone().strftime('%d.%m.%Y')})
        return promocodes
    async def get_all_promocodes_dev(self):
        promocodes_set = await self.promocodes.filter(is_active=True)
        promocodes = []
        for i in promocodes_set:
            if i.end_day > datetime.now(timezone.utc) and i.count!=0:
                promocodes.append({'id': i.id,
                                   'promocode': i.short_name,
                                   'type': i.type,
                                   'effect': i.effect,
                                   #'works_with' : await i.get_product_categories_id(),
                                   'minimal_sum': i.min_sum,
                                   'expires_at': i.end_day})
        return promocodes


class UserJWT(Model):
    user = fields.ForeignKeyField('models.User', pk=True)
    refresh_code = fields.CharField(max_length=255)
    is_active = fields.BooleanField()

class UserBlacklist(Model):
    user_id = fields.IntField()