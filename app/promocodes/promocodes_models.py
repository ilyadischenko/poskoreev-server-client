from tortoise import fields
from tortoise.models import Model
class PromoCode(Model):
    id=fields.IntField(pk=True)
    promocode=fields.CharField
    name=fields.CharField
    expires_at=fields.DateField