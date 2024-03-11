import datetime
import json
from urllib import request

from fastapi import HTTPException, APIRouter, Request, Response
from app.restaurants.models import Restaurant, Address, City
from app.orders.models import Order, OrderLog
restaurant_router = APIRouter(
    prefix="/api/v1/restaurants"
)


@restaurant_router.get('/getCities', tags=['Restaurants'])
async def get_cities():
    # add sort
    query = await City.all().values('id', 'name')
    query.sort(key=lambda i : i['name'])
    return query


@restaurant_router.post('/setcity', tags=['Restaurants'])
async def set_city(city: int, request: Request, response: Response):
    # проверить на наличие рестика
    print(1)
    query = await City.get_or_none(id=city)
    if query is None: raise HTTPException(status_code=404, detail='City not found')
    if '_ci' in request.cookies and int(request.cookies['_ci'])!=city:
        response.delete_cookie('_si')
        response.delete_cookie('_ri')
        if '_oi' in request.cookies:
            # await Order.filter(id=int(request.cookies['_oi'])).delete()
            # await OrderLog.filter(order_id=int(request.cookies['_oi'])).delete()
            response.delete_cookie('_oi')
    response.set_cookie('_ci', str(city), httponly=True, samesite='none', secure=True)
    return query


@restaurant_router.get('/getstreets', tags=['Restaurants'])
async def get_streets(request: Request):
    if '_ci' not in request.cookies:
        raise HTTPException(status_code=404, detail='pick city')
    query = await Address.filter(city_id=int(request.cookies['_ci']), available=True).values('street', 'id')
    query.sort(key=lambda i : i['street'])
    return query


@restaurant_router.post('/setstreet', tags=['Restaurants'])
async def set_street(street: int, request: Request, response: Response):
    if '_ci' not in request.cookies:
        raise HTTPException(status_code=404, detail='pick city')
    street_query = await Address.get_or_none(id=int(street), available=True, city_id=int(request.cookies['_ci']))
    if street_query is None:
        raise HTTPException(status_code=404, detail='street not found')
    if '_ri' in request.cookies and '_oi' in request.cookies and street_query.restaurant_id!=int(request.cookies['_ri']):
        # await Order.filter(id=int(request.cookies['_oi'])).delete()
        # await OrderLog.filter(order_id=int(request.cookies['_oi'])).delete()
        print(123)
        response.delete_cookie('_oi', httponly=True, samesite='none', secure=True)
    response.set_cookie('_ri', str(street_query.restaurant_id), httponly=True, samesite='none', secure=True)
    response.set_cookie('_si', str(street), httponly=True, samesite='none', secure=True)
    return street_query

@restaurant_router.get('/', tags=['Restaurants'])
async def get_restaurant_info(request: Request):
    if not '_ri' in request.cookies or not '_si': raise HTTPException(status_code=404, detail='no restaurant set')
    restaurant = await Restaurant.get(id=int(request.cookies['_ri']))
    street = await Address.get(id=int(request.cookies['_si']))
    if not restaurant: raise HTTPException(status_code=404, detail=f"Restaurant {request.cookies['_ri']} not found")
    return {"open": restaurant.open, "closed": restaurant.closed, "working": restaurant.working,
            "min_sum": restaurant.min_sum, "restaurant_address": restaurant.address, "client_address": street.street}