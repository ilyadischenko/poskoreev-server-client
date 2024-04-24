import random

import requests


async def send_sms(number):
    print(number)
    print('7'+str(number)[1:])
    payload = {
        'service_id': 446,
        'secret_key': 'cd0413a8f095e312e3392ccd7fd8dff3',
        'phone': '7' + str(number)[1:],
        'nowait': 1,
        'test': 0
    }

    resp = requests.get('https://api.nerotech.ru/api/v1/call', params=payload).json()
    if resp['status']:
        return resp['code']
    else:
        return False


def very_complex_function_to_generate_code():
    rng = random.SystemRandom()
    code = rng.randrange(1000, 10000)
    return code
