from tortoise import fields
from tortoise.models import Model
class User(Model):
    id=fields.IntField(pk=True)
    phone=fields.CharField(unique=True,null=False,max_length=255)
    email=fields.CharField(max_length=255,unique=True,null=True)
    telegram=fields.CharField(max_length=255,unique=True,null=True)
    birthday=fields.DateField(null=True)
    promocodes=fields.ManyToManyField('models.PromoCodePercent')
    bonuses=fields.IntField(default=0,ge=0)
    code=fields.CharField(max_length=255)
    time_expires=fields.DatetimeField()