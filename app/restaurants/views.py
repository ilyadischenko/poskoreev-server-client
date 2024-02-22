import datetime

from fastapi import HTTPException, APIRouter, Request, Response
from app.restaurants.models import Restaurant, Address, Cities

restaurant_router = APIRouter()


@restaurant_router.get('/getcities', tags=['Restaurants'])
async def get_cities():
    # add sort
    return await Cities.all()


@restaurant_router.post('/setcity', tags=['Restaurants'])
async def set_city(city: int, response: Response):
    # проверить на наличие рестика
    query = await Cities.get_or_none(id=city)
    if query is None: raise HTTPException(status_code=404, detail='City not found')
    response.set_cookie('_ci', city, httponly=True, samesite='none', secure=True)


@restaurant_router.get('/getstreets', tags=['Restaurants'])
async def get_streets(request: Request):
    if '_ci' not in request.cookies:
        raise HTTPException(status_code=404, detail='pick city')

    return await Address.filter(city_id=int(request.cookies['_ci']), available=True).values('street', 'id')


@restaurant_router.post('/setstreet', tags=['Restaurants'])
async def set_street(street: int, request: Request, response: Response):
    if '_ci' not in request.cookies:
        raise HTTPException(status_code=404, detail='pick city')

    street_query = await Address.get_or_none(id=int(street), available=True, city_id=int(request.cookies['_ci']))
    if street_query is None:
        raise HTTPException(status_code=404, detail='street not found')

    response.set_cookie('_ri', str(street_query.restaurant_id))
    response.set_cookie('_si', str(street))

    return street_query

