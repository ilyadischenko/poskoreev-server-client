from tortoise import fields
from tortoise.models import Model
class PromoCodePercent(Model):
    id=fields.IntField(pk=True)
    short_name=fields.CharField(max_length=255)
    description=fields.CharField(max_length=255, null=True)
    discount=fields.DecimalField(max_digits=4, decimal_places=2,default=00.00)
    for_all=fields.BooleanField(default=False)
    start=fields.DatetimeField()
    end=fields.DatetimeField()

#class PromoCodeConst(Model): pass
#class PromoCodeSpecial(Model): pass