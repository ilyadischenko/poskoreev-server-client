import datetime

from tortoise import fields
from tortoise.models import Model
from tortoise.fields import JSONField

class Order(Model):
    id = fields.IntField(pk=True, auto_increment=True)
    user = fields.ForeignKeyField('models.User')
    #restaurant = fields.ForeignKeyField('models.Restaurant', related_name='restaurant')
    # 0 - inside 1 - delivery 2 - pickup
    type = fields.IntField(default=1)
    invalid_at = fields.DatetimeField()
    added_bonuses=fields.IntField(ge=0, default=0)
    promocode = fields.CharField(max_length=255, null=True)
    promocode_valid = fields.BooleanField(default=False)
    #0 - canceled 1 - success completion 2 - in progress, 3 expired
    status = fields.IntField(default=2)
    # 0 - наличные, 1 - картой при получении, 2 - картой на сайте (пока не делаем функционал)
    pay_type = fields.IntField(default=1)
    #address = fields.ForeignKeyField('models.Address')
    products_count = fields.IntField(ge=0, default=0)
    sum = fields.FloatField(ge=0, default=0)
    total_sum = fields.FloatField(ge=0, default=0)

class CartItem(Model):
    order = fields.ForeignKeyField('models.Order')
    menu = fields.ForeignKeyField('models.Menu')
    product = fields.ForeignKeyField('models.Product')
    quantity = fields.IntField(ge=0,default=0)
    sum = fields.FloatField(ge=0,default=0)
    bonuses = fields.IntField(ge=0,default=0)

class OrderLog(Model):
    order_id = fields.IntField()
    items = fields.JSONField(null=True)
    type = fields.IntField(default=1)
    canceled_at = fields.DatetimeField(null=True)
    paid_at = fields.DatetimeField(null=True)
    success_completion_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)