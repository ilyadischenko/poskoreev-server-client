from tortoise import Model, fields

class Cities(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, default='')


class Address(Model):
    id = fields.IntField(pk=True)
    street = fields.CharField(max_length=255, unique=True)
    available = fields.BooleanField(default=True)
    restaurant = fields.ForeignKeyField('models.Restaurant')
    city = fields.ForeignKeyField('models.Cities')



class Restaurant(Model):
    id = fields.IntField(pk=True)
    open = fields.TimeField(null=False, timezone=True)
    closed = fields.TimeField(null=False, timezone=True)
    address = fields.CharField(max_length=255, unique=False)
    delivery = fields.BooleanField(default=True)
    pickup = fields.BooleanField(default=False)
    inside = fields.BooleanField(default=False)
    working = fields.BooleanField(default=True)
    city = fields.ForeignKeyField('models.Cities')
    min_sum = fields.IntField(default=0, ge=0)


