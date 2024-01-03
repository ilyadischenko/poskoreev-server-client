from tortoise import fields
from tortoise.models import Model
from app.promocodes.promocodes_models import PromoCode
class User(Model):
    id=fields.IntField(pk=True)
    phone=fields.CharField(unique=True,null=False)
    email=fields.CharField(max_length=255,unique=True)
    telegram=fields.CharField(max_length=255,unique=True)
    #birthday=fields.DateField
    promocodes=fields.ManyToManyField('PromoCode',related_name='users')
    bonuses=fields.IntField(default=0,ge=0)
    code=fields.IntField
    time_expires=fields.TimeField