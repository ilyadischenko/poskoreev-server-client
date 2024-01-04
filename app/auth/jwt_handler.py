import time
import jwt
from decouple import config
jwt_secret=config('secret')
jwt_algorithm=config('algorithm')
async def generateJWT(number: str, time_token : int):
    payload = {
        "number": number,
        "expires": time.time() + time_token
    }
    token = await jwt.encode(payload, jwt_secret, algorithm=jwt_algorithm)

    return token

async def decodeJWT(token: bytes):
    decoded_token = await jwt.decode(token, jwt_secret, algorithms=[jwt_algorithm])
    return decoded_token if decoded_token["expires"] >= time.time() else None