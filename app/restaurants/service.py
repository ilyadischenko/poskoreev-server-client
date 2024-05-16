import pytz
from datetime import datetime

from fastapi import HTTPException, Request

from app.app.jwtService import decodeJWT


def time_with_tz(time: datetime, tz: str):
    date = datetime.now().date()
    combined_datetime = datetime.combine(date, time)
    return combined_datetime.astimezone(pytz.timezone(tz)).time()


def datetime_with_tz(datetime: datetime, tz: str):
    return datetime.astimezone(pytz.timezone(tz))


class CookieCheckerCity:
    async def __call__(self, request: Request):
        if '_ci' not in request.cookies: raise HTTPException(status_code=400, detail={
            'status': 202,
            'message': "Пожалуйста, выберите город"
        })
        return int(request.cookies['_ci'])


class CookieCheckerRestaurant:
    async def __call__(self, request: Request):
        if '_ri' not in request.cookies: raise HTTPException(status_code=400, detail={
            'status': 206,
            'message': "Пожалуйста, выберите ресторан"
        })
        return int(request.cookies['_ri'])


class CookieCheckerAddress:
    async def __call__(self, request: Request):
        if '_picked_address' not in request.cookies: raise HTTPException(status_code=400, detail={
            'status': 204,
            'message': "Пожалуйста, выберите улицу"
        })
        x = decodeJWT(request.cookies['_picked_address'])
        return x


CCC = CookieCheckerCity()
CCR = CookieCheckerRestaurant()
CCA = CookieCheckerAddress()
