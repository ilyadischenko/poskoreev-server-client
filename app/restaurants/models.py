from tortoise import Model, fields

class Address(Model):
    id = fields.IntField(pk=True)
    street = fields.CharField(max_length=255, unique=True)
    available = fields.BooleanField(default=True)
    restaurant= fields.ForeignKeyField('models.Restaurant')


class Restaurant(Model):
    id = fields.IntField(pk=True)
    open = fields.TimeField(null=False, timezone=True)
    closed = fields.TimeField(null=False, timezone=True)
    address = fields.CharField(max_length=255, unique=True)
    delivery = fields.BooleanField(default=True)
    pickup = fields.BooleanField(default=False)
    inside = fields.BooleanField(default=False)
    working = fields.BooleanField(default=True)
    city = fields.CharField(default='Орёл', max_length=255)
    min_sum = fields.IntField(default=0, ge=0)


