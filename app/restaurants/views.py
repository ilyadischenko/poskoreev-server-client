import datetime
import json
from urllib import request

from fastapi import HTTPException, APIRouter, Request, Response
from app.restaurants.models import Restaurant, Address, City, RestaurantPayType
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
    query = await City.get_or_none(id=city)
    if query is None: raise HTTPException(status_code=404, detail='City not found')
    if '_ci' in request.cookies and int(request.cookies['_ci'])!=city:
        response.delete_cookie('_si', httponly=True)
        response.delete_cookie('_ri', httponly=True)
        if '_oi' in request.cookies:
            response.delete_cookie('_oi')
    response.set_cookie('_ci', str(city), httponly=True, secure=True, samesite='none')
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
    r = await Restaurant.get(id=street_query.restaurant_id)
    if not r.delivery: raise HTTPException(status_code=400, detail='unfortunately the restaurant that serves your street temporally doesnt deliver')
    if '_ri' in request.cookies and '_oi' in request.cookies and r.id!=int(request.cookies['_ri']):
        response.delete_cookie('_oi', httponly=True, samesite='none', secure=True)
    response.set_cookie('_ri', str(r.id), httponly=True, secure=True, samesite='none')
    response.set_cookie('_si', str(street), httponly=True, secure=True, samesite='none')
    return street_query

@restaurant_router.get('/paytypes', tags=['Restaurants'])
async def get_restaurant_info(request: Request):
    if not '_ri' in request.cookies or not '_si': raise HTTPException(status_code=404, detail='no restaurant set')
    restaurant = await Restaurant.get(id=int(request.cookies['_ri']))
    rpt_query = await RestaurantPayType.filter(restaurant_id=restaurant.id, available=True).prefetch_related('pay_type')
    rpt_list=[{'id': rpt.pay_type_id, 'name': rpt.pay_type.name} for rpt in rpt_query]
    return rpt_list


@restaurant_router.get('/', tags=['Restaurants'])
async def get_restaurant_info(request: Request):
    if not '_ri' in request.cookies or not '_si': raise HTTPException(status_code=404, detail='no restaurant set')
    restaurant = await Restaurant.get(id=int(request.cookies['_ri']))
    street = await Address.get(id=int(request.cookies['_si']))
    if not restaurant: raise HTTPException(status_code=404, detail=f"Restaurant {request.cookies['_ri']} not found")
    rpt_query = await RestaurantPayType.filter(restaurant_id=restaurant.id, available=True).prefetch_related('pay_type')
    rpt_list=[{'id': rpt.pay_type_id, 'name': rpt.pay_type.name} for rpt in rpt_query]
    return {"open": restaurant.open, "closed": restaurant.closed, "working": restaurant.working, "pay_types": rpt_list,
            "min_sum": restaurant.min_sum, "restaurant_address": restaurant.address, "client_address": street.street}