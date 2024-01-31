# import time
import jwt
from decouple import config

jwt_secret = config('secret')
jwt_algorithm = config('algorithm')


async def generateJWT(
        id: int,
        # time_token_seconds: int
):
    payload = {
        "id": id,
        # "expires": time.time() + time_token_seconds
    }
    token = jwt.encode(payload, jwt_secret, algorithm=jwt_algorithm)
    return token


async def decodeJWT(token: str):
    decoded_token = jwt.decode(token, jwt_secret, algorithms=[jwt_algorithm])
    # if decoded_token["expires"] >= time.time() else None
    return decoded_token


