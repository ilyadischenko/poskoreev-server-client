import re

from fastapi import HTTPException, Request

from app.app.response import getResponseBody
from app.auth.jwt_handler import decodeJWT
from app.users.models import User


async def validate_number(phone_number):
    pattern = re.compile(r'^(?:\+7|\b8)\d{10}$')
    if re.match(pattern, phone_number):
        if (phone_number[0] == "+"):
            return phone_number[2::]
        return phone_number[1::]
    raise HTTPException(status_code=200, detail={
                'status': 103,
                'message': "Не валидный номер"
            })


class AuthGuard:
    async def __call__(self, request: Request):
        if '_at' not in request.cookies:
            raise HTTPException(status_code=401, detail={
                'status': 101,
                'message': "Запрещено"
            })

        decoded_code = await decodeJWT(request.cookies.get('_at'))
        if not decoded_code: raise HTTPException(status_code=401, detail={
            'status': 102,
            'message': "Не авторизован"
        })
        return decoded_code['id']


auth = AuthGuard()

class NewAuthGuard:
    async def __call__(self, request: Request):
        if '_at' not in request.cookies:
            raise HTTPException(status_code=200, detail=getResponseBody(
                status=False,
                errorCode=101,
                errorMessage='Для начала нужно авторизоваться'
            ))


        decoded_code = await decodeJWT(request.cookies.get('_at'))
        if not decoded_code:
            raise HTTPException(status_code=200, detail=getResponseBody(
                status=False,
                errorCode=101,
                errorMessage='Для начала нужно авторизоваться'
            ))

        return decoded_code['id']


newAuth = NewAuthGuard()

class GetDecodedUserIdOrNone:
    async def __call__(self, request: Request):
        if '_at' not in request.cookies:
            return None

        decoded_code = await decodeJWT(request.cookies.get('_at'))
        if not decoded_code:
            return None
        return decoded_code['id']


getUserId = GetDecodedUserIdOrNone()


