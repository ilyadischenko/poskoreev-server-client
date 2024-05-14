import jwt
from decouple import config

jwt_secret = config('secret')
jwt_algorithm = config('algorithm')


def generateJWT(
        payload: dict
):
    token = jwt.encode(payload, jwt_secret, algorithm=jwt_algorithm)
    return token


def decodeJWT(jwtstr: str):
    return jwt.decode(jwtstr, jwt_secret, algorithms=[jwt_algorithm])