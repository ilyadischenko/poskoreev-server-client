import datetime
from users_views import write_code, get_code
from app.auth.jwt_handler import signJWT, decodeJWT

async def send_sms(number : str):
    code=1234
    await write_code(number, code)
    return code

async def confirm_sms(number, code):
    code, time = await get_code(number)
    if code == code and time > datetime.datetime.now():
        return True
    else: return False