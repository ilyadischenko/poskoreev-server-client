import random
import requests

from app.telegram.main import send_access_call_message


# async def send_sms(number):
#     payload = {
#         'service_id': 446,
#         'secret_key': 'cd0413a8f095e312e3392ccd7fd8dff3',
#         'phone': '7' + str(number)[1:],
#         'nowait': 0,
#         'test': 0
#     }
#     resp = requests.get('https://api.nerotech.ru/api/v1/call', params=payload).json()
#     if resp['status']:
#         await send_access_call_message(number)
#         return resp['code']
#     else:
#         await send_error_auth_message(number, resp['error'])
#         return False


def very_complex_function_to_generate_code():
    rng = random.SystemRandom()
    code = rng.randrange(1000, 10000)
    return code
