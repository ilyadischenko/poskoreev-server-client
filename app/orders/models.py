from tortoise import fields
from tortoise.models import Model

class Order(Model):
    user = fields.ForeignKeyField('models.User')
    #restaurant = fields.ForeignKeyField('models.Restaurant', related_name='restaurant')
    products = fields.ManyToManyField('models.Menu')
    type = fields.ForeignKeyField('models.OrderType')
    order_time = fields.DatetimeField()
    added_bonuses=fields.IntField(ge=0)
    promocode = fields.ForeignKeyField('models.PromoCodePercent', null=True)
    status = fields.ForeignKeyField('models.OrderStatus')
    #address = fields.ForeignKeyField('models.Address')
    products_count = fields.IntField(ge=0)
    sum = fields.FloatField(ge=0)
    total_sum = fields.FloatField(ge=0)

class OrderType(Model):
    id = fields.IntField(pk=True)
    type = fields.CharField(max_length=255, unique=True)

class OrderStatus(Model):
    id = fields.IntField(pk=True)
    status = fields.CharField(max_length=255, unique=True)

class CartItem(Model):
    product = fields.ForeignKeyField('models.Menu', unique=True)
    quantity = fields.IntField(ge=0,default=0)
    sum = fields.FloatField(ge=0,default=0)

class Cart(Model):
    user = fields.ForeignKeyField('models.User')
    items = fields.ManyToManyField('models.CartItem')
    sum = fields.FloatField(ge=0, default=0)