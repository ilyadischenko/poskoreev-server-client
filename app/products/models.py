from tortoise import fields
from tortoise.models import Model


class Product(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255, null=False)
    description = fields.CharField(max_length=255, null=True)
    img = fields.CharField(max_length=255, null=True)


class Menu(Model):
    id = fields.IntField(pk=True)
    product = fields.ForeignKeyField('models.Product', related_name='product')
    restaurant = fields.ForeignKeyField('models.Restaurant')
    category = fields.ForeignKeyField('models.ProductCategory', related_name='category')
    price = fields.IntField(ge=0, default=0)
    unit = fields.CharField(max_length=255, default=0)
    size = fields.IntField(ge=0, default=0)
    bonuses = fields.IntField(ge=0, default=0)
    visible = fields.BooleanField(default=True)
    in_stock = fields.BooleanField(default=True)


class ProductCategory(Model):
    id = fields.IntField(pk=True)
    type = fields.CharField(max_length=255, unique=True)
