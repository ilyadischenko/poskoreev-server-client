import datetime

from fastapi import HTTPException, APIRouter, Request, Response
from app.restaurants.models import Restaurant, Address, City
from app.orders.models import Order, OrderLog
restaurant_router = APIRouter()


@restaurant_router.get('/getCities', tags=['Restaurants'])
async def get_cities():
    # add sort
    return await City.all()


@restaurant_router.post('/setCity', tags=['Restaurants'])
async def set_city(city: int, request: Request, response: Response):
    # проверить на наличие рестика
    query = await City.get_or_none(id=city)
    if query is None: raise HTTPException(status_code=404, detail='City not found')
    if '_ci' in request.cookies and int(request.cookies['_ci'])!=city:
        response.delete_cookie('_si')
        response.delete_cookie('_ri')
        if '_oi' in request.cookies:
            await Order.filter(id=int(request.cookies['_oi'])).delete()
            await OrderLog.filter(order_id=int(request.cookies['_oi'])).delete()
            response.delete_cookie('_oi')
    response.set_cookie('_ci', str(city), httponly=True, samesite='none', secure=True)
    return query


@restaurant_router.get('/getStreets', tags=['Restaurants'])
async def get_streets(request: Request):
    if '_ci' not in request.cookies:
        raise HTTPException(status_code=404, detail='pick city')

    return await Address.filter(city_id=int(request.cookies['_ci']), available=True).values('street', 'id')


@restaurant_router.post('/setStreet', tags=['Restaurants'])
async def set_street(street: int, request: Request, response: Response):
    if '_ci' not in request.cookies:
        raise HTTPException(status_code=404, detail='pick city')
    street_query = await Address.get_or_none(id=int(street), available=True, city_id=int(request.cookies['_ci']))
    if street_query is None:
        raise HTTPException(status_code=404, detail='street not found')
    if '_ri' in request.cookies and '_oi' in request.cookies and street_query.restaurant_id!=int(request.cookies['_ri']):
        # await Order.filter(id=int(request.cookies['_oi'])).delete()
        # await OrderLog.filter(order_id=int(request.cookies['_oi'])).delete()
        response.delete_cookie('_oi')
    response.set_cookie('_ri', str(street_query.restaurant_id))
    response.set_cookie('_si', str(street))

    return street_query

