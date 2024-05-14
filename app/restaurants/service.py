import pytz
from datetime import datetime

from fastapi import HTTPException, Request


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


class CookieCheckerStreet:
    async def __call__(self, request: Request):
        if '_si' not in request.cookies: raise HTTPException(status_code=400, detail={
            'status': 204,
            'message': "Пожалуйста, выберите улицу"
        })
        return int(request.cookies['_si'])


CCC = CookieCheckerCity()
CCR = CookieCheckerRestaurant()
CCS = CookieCheckerStreet()
