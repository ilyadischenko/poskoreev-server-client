import pytz
from datetime import datetime

def time_with_tz(time : datetime, tz : str):
    date = datetime.now().date()
    combined_datetime = datetime.combine(date, time)
    return combined_datetime.astimezone(pytz.timezone(tz)).time()

def datetime_with_tz(datetime : datetime, tz : str):
    return datetime.astimezone(pytz.timezone(tz))