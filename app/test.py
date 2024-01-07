import datetime
from tzlocal import get_localzone
from pytz import timezone

timestamp = 1707229331.4954493

# Convert the timestamp to a datetime object
datetime_object1 = datetime.datetime.now().astimezone()
datetime_object2 = datetime_object1.astimezone()

print(datetime_object1,datetime_object2)
