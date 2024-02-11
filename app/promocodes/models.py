from tortoise import fields
from tortoise.models import Model

class PromoCodeModel(Model):
    id = fields.IntField(pk=True)
    short_name = fields.CharField(max_length=255)
    description = fields.CharField(max_length=255, null=True)

class PromoCodeType(Model):
    id = fields.IntField(pk=True)
    type = fields.CharField(max_length=255)

class PromoCode(Model):
    id = fields.IntField(pk=True)
    promocode = fields.ForeignKeyField('models.PromoCodeModel')
    type = fields.ForeignKeyField('models.PromoCodeType')
    #count = fields.IntField(null=True)
    discount = fields.FloatField()
    for_all = fields.BooleanField(default=False)
    start_day = fields.DatetimeField()
    end_day = fields.DatetimeField()
    min_sum = fields.FloatField(null=True)
    #works_with = fields.ManyToManyField('models.ProductCategory',null=True)
    is_active = fields.BooleanField(default=True)