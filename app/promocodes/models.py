from tortoise import fields
from tortoise.models import Model


class PromoCodePercent(Model):
    id = fields.IntField(pk=True)
    short_name = fields.CharField(max_length=255)
    description = fields.CharField(max_length=255, null=True)
    count = fields.IntField(null=True)
    for_all = fields.BooleanField(default=False)
    discount = fields.DecimalField(max_digits=4, decimal_places=2, default=00.00)
    start_day = fields.DatetimeField()
    end_day = fields.DatetimeField()
    min_sum = fields.IntField(null=True)
    is_active = fields.BooleanField(default=True)

# class PromoCodeConst(Model): pass
# class PromoCodeSpecial(Model): pass
