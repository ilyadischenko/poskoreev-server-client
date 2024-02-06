from tortoise import fields
from tortoise.models import Model

class Order(Model):
    user = fields.OneToOneField('models.User')
    #restaurant = fields.ForeignKeyField('models.Restaurant', related_name='restaurant')
    items = fields.ManyToManyField('models.CartItem')
    # 0 - inside 1 - delivery 2 - pickup
    type = fields.IntField(default=1)
    invalid_at = fields.DatetimeField()
    #time = fields.DatetimeField()
    added_bonuses=fields.IntField(ge=0, default=0)
    #promocode = fields.ForeignKeyField('models.PromoCodePercent', null=True)
    #0 - canceled 1 - paid 2 - in progress
    status = fields.IntField(default=2)
    #address = fields.ForeignKeyField('models.Address')
    products_count = fields.IntField(ge=0, default=0)
    sum = fields.FloatField(ge=0, default=0)
    #total_sum = fields.FloatField(ge=0, default=0)

class CartItem(Model):
    user = fields.ForeignKeyField('models.User')
    product = fields.ForeignKeyField('models.Menu')
    quantity = fields.IntField(ge=0,default=0)
    sum = fields.FloatField(ge=0,default=0)