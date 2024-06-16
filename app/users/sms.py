import json
import random
import requests

from app.telegram.main import send_access_call_message, send_error_sms_auth_message

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


def very_complex_function_to_generate_code():
    rng = random.SystemRandom()
    code = rng.randrange(1000, 10000)
    return code
