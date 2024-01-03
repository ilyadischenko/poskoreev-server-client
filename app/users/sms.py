import datetime
from users_views import write_code, get_code

async def send_sms(number):
    return await write_code(number, 1234)

async def confirm_sms(number, code):
    code, time = await get_code(number)
    if code == code and time > datetime.datetime.now():
        #...
        return