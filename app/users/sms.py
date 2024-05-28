import json
import random
import requests

from app.telegram.main import send_error_auth_message, send_access_call_message, send_error_sms_auth_message

import hashlib
import time
import requests

login = 'poskoreev'
ts = '123213213fcsac'
api_key = 'ZzxoFrQWEnYjVXYFamFNKtuS'
secret = hashlib.md5((ts + api_key).encode()).hexdigest()

headers = {
    'login': login,
    'ts': ts,
    'secret': secret,
    'Content-type': 'application/json',
}

async def sendSMS(phoneNumber, code):
    data = {
        'route': 'sms',
        'from': 'Poskoreev',
        'to': f'+{phoneNumber}',
        'text': f'Код - {code} - poskoreev.ru'
    }

    r = requests.post('https://cp.redsms.ru/api/message', headers=headers, data=json.dumps(data)).json()
    if not r['success']:
        await send_error_sms_auth_message(phoneNumber, str(r['errors']))
    else:
        await send_access_call_message(phoneNumber)


# async def send_sms(number):
#     payload = {
#         'service_id': 447,
#         'secret_key': 'cd0413a8f095e312e3392ccd7fd8dff3',
#         # 'secret_key': 'dda67dcd4cb4fa8d1800c116e13b3e83',
#         'phone': '7' + str(number)[1:],
#         # 'nowait': 1,
#         'test': 0
#     }
#     resp = requests.get('https://api.nerotech.ru/api/v1/call', params=payload).json()
#     print(resp)
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
