import datetime

from tortoise import fields
from tortoise.models import Model
from tortoise.fields import JSONField


class Order(Model):
    id = fields.IntField(pk=True, auto_increment=True)
    user = fields.ForeignKeyField('models.User')
    restaurant = fields.ForeignKeyField('models.Restaurant')
    # 0 - inside 1 - delivery 2 - pickup
    type = fields.IntField(default=1)
    invalid_at = fields.DatetimeField()
    added_bonuses = fields.IntField(ge=0, default=0)
    # -1 истек срок
    # 0 в процессе создания
    # 1 ожидает подтверждение менеджера
    # 2 принят
    # 3 успешно доставлен (или в ресторане отдан)
    # 4 отменен
    status = fields.IntField(default=0)
    products_count = fields.IntField(ge=0, default=0)
    sum = fields.FloatField(ge=0, default=0)
    total_sum = fields.FloatField(ge=0, default=0)

    address = fields.ForeignKeyField('models.Address')
    house = fields.CharField(max_length=255, null=True)
    entrance = fields.CharField(max_length=255, null=True)
    floor = fields.CharField(max_length=255, null=True)
    apartment = fields.CharField(max_length=255, null=True)
    comment = fields.CharField(max_length=255, null=True)

    promocode = fields.CharField(null=True, max_length=255)
    promocode_applied = fields.BooleanField(default=False)
    promocode_linked = fields.BooleanField(default=False)
    rating = fields.IntField(null=True, ge=1, le=5)


class CartItem(Model):
    order = fields.ForeignKeyField('models.Order')
    menu = fields.ForeignKeyField('models.Menu')
    product = fields.ForeignKeyField('models.Product')
    quantity = fields.IntField(ge=0, default=0)
    sum = fields.FloatField(ge=0, default=0)
    bonuses = fields.IntField(ge=0, default=0)


class OrderPayType(Model):
    order = fields.ForeignKeyField('models.Order')
    restaurant_pay_type = fields.ForeignKeyField('models.RestaurantPayType')


class OrderLog(Model):
    order_id = fields.IntField()
    items = fields.JSONField(null=True)
    # -1 в процессе
    # 1 начали готовить
    # 2 доставляют
    # 3 доставлен

    # 4 менеджер сказал фейк(опционально)
    status = fields.IntField(default=-1)
    created_at = fields.DatetimeField(auto_now_add=True)
    canceled_at = fields.DatetimeField(null=True)
    start_cooking = fields.DatetimeField(null=True)
    start_delivering = fields.DatetimeField(null=True)
    success_completion_at = fields.DatetimeField(null=True)

