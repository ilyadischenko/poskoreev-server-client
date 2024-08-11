from tortoise import fields
from tortoise.models import Model


class PromoCode(Model):
    id = fields.IntField(pk=True, auto_increment=True)
    restaurant = fields.ForeignKeyField('models.Restaurant', null=True, default=None)
    short_name = fields.CharField(max_length=255, null=False, unique=True)
    description = fields.CharField(max_length=255, null=True)
    # 1 - продукт, 2 - процент, 3 - рубли
    type = fields.IntField(default=2)
    count = fields.IntField(default=1, null=False)
    effect = fields.IntField(default=1, null=False)
    for_all = fields.BooleanField(default=False)
    start_day = fields.DatetimeField()
    end_day = fields.DatetimeField()
    min_sum = fields.IntField(null=True)
    is_active = fields.BooleanField(default=True)
    only_mobile = fields.BooleanField(default=False)


class PromocodeProduct(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255, null=False)
    description = fields.CharField(max_length=255, null=True)
    img = fields.CharField(max_length=255, null=True)
    price = fields.IntField(ge=0, default=0)
    unit = fields.CharField(max_length=255, default=0)
    size = fields.IntField(ge=0, default=0)
