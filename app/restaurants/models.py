from tortoise import Model, fields

class Address(Model):
    id = fields.IntField(pk=True)
    adress = fields.CharField(max_length=255)
    working = fields.BooleanField(default=False)
    min_sum = fields.IntField(default=0, ge=0)


class Restaurant(Model):
    id = fields.IntField(pk=True)
    open = fields.TimeField(null=False)
    closed = fields.TimeField(null=False)
    address = fields.ForeignKeyField('models.Address', null=True)
    delivery = fields.BooleanField(default=True)
    pickup = fields.BooleanField(default=False)
    inside = fields.BooleanField(default=False)
    working = fields.BooleanField(default=True)
    city = fields.CharField(default='Орёл', null=True, max_length=255)
    timezone = fields.CharField(max_length=255)
    min_sum = fields.IntField(default=0, ge=0)


