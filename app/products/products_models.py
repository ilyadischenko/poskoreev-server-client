from tortoise import fields
from tortoise.models import Model
from datetime import datetime, timezone


class Products(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255, null=False)
    description = fields.CharField(max_length=255, null=True)
    img = fields.CharField(max_length=255, null=True)


class Menu(Model):
    id = fields.IntField(pk=True)
    product = fields.ForeignKeyField('models.Products', related_name='product')
    # restaurant_id = fields.OneToOneField('models.Restaurant')
    categories = fields.ForeignKeyField('models.ProductsCategories', to_field='id', related_name='categories')
    price = fields.IntField(ge=0)
    quantity = fields.IntField(ge=0)
    size = fields.IntField(ge=0, default=0)
    bonuses = fields.IntField(ge=0, default=0)
    is_view = fields.BooleanField(default=True)
    is_have = fields.BooleanField(default=True)


class ProductsCategories(Model):
    id = fields.IntField(pk=True)
    type = fields.CharField(max_length=255, unique=True)
