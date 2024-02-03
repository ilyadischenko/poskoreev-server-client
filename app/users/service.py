import re

from fastapi import HTTPException, Request

from app.auth.jwt_handler import decodeJWT


async def validate_number(phone_number):
    pattern = re.compile(r'^(?:\+7|\b8)\d{10}$')
    if re.match(pattern, phone_number):
        if(phone_number[0]=="+"):
            return phone_number[2::]
        return phone_number[1::]
    raise HTTPException(status_code=400, detail="these r some random numbers")

class AuthGuard:
    async def __call__(self, request: Request):
        if '_at' not in request.cookies:
            raise HTTPException(status_code=401, detail="Запрещено")

        decoded_code = await decodeJWT(request.cookies.get('_at'))
        if not decoded_code: raise HTTPException(status_code=401, detail="Не авторизован")
        return decoded_code['id']


auth = AuthGuard()