from tortoise import fields
from tortoise.models import Model
from datetime import datetime, timezone


class Product(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255, null=False)
    description = fields.CharField(max_length=255, null=True)
    img = fields.CharField(max_length=255, null=True)


class Menu(Model):
    id = fields.IntField(pk=True)
    product = fields.ForeignKeyField('models.Product', related_name='product')
    # restaurant_id = fields.OneToOneField('models.Restaurant')
    category = fields.ForeignKeyField('models.ProductCategory', to_field='id', related_name='category')
    price = fields.IntField(ge=0)
    quantity = fields.IntField(ge=0)
    size = fields.IntField(ge=0, default=0)
    bonuses = fields.IntField(ge=0, default=0)
    visible = fields.BooleanField(default=True)
    in_stock = fields.BooleanField(default=True)


class ProductCategory(Model):
    id = fields.IntField(pk=True)
    type = fields.CharField(max_length=255, unique=True)
