import random

from greensms.client import GreenSMS

async def send_sms():
    code=very_complex_function_to_generate_code()
    client = GreenSMS(user='test', password='test')
    response = client.call.send(to='79155188088')
    print(response)
    sms=True
    if(sms):
        return code
    else: return False
    
def very_complex_function_to_generate_code():
    rng = random.SystemRandom()
    code = rng.randrange(1000,10000)
    return code
