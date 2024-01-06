from datetime import datetime,timezone,timedelta
from tzlocal import get_localzone # $ pip install tzlocal
import time

start = datetime.now(tz=get_localzone())
finish = start + timedelta(days=7)
print(start,finish)