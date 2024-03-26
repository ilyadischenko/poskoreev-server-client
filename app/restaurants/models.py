from tortoise import Model, fields


class City(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, default='')


class Address(Model):
    id = fields.IntField(pk=True)
    street = fields.CharField(max_length=255, unique=True)
    available = fields.BooleanField(default=True)
    restaurant = fields.ForeignKeyField('models.Restaurant')
    city = fields.ForeignKeyField('models.City')


class Restaurant(Model):
    id = fields.IntField(pk=True)
    open = fields.TimeField(null=False, timezone=True)
    closed = fields.TimeField(null=False, timezone=True)
    address = fields.CharField(max_length=255, unique=False)
    delivery = fields.BooleanField(default=True)
    pickup = fields.BooleanField(default=False)
    inside = fields.BooleanField(default=False)
    working = fields.BooleanField(default=True)
    city = fields.ForeignKeyField('models.City')
    min_sum = fields.IntField(default=0, ge=0)
    need_valid_sum = fields.IntField(default=3000, ge=0)
    max_sum = fields.IntField(default=20000, ge=0)
    timezoneutc = fields.CharField(default='Moscow', max_length=255)


class PayType(Model):
    #1 - нал, 2 - картой при получении, 3 - предоплата
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    eng_name = fields.CharField(max_length=255)


class RestaurantPayType(Model):
    id = fields.IntField(pk=True)
    restaurant = fields.ForeignKeyField('models.Restaurant')
    pay_type = fields.ForeignKeyField('models.PayType')
    available = fields.BooleanField()
