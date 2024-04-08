import datetime
import json
from urllib import request
from fastapi import HTTPException, APIRouter, Request, Response
from app.restaurants.models import Restaurant, Address, City, RestaurantPayType
from app.restaurants.service import time_with_tz
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
    if query is None: raise HTTPException(status_code=404, detail={
                'status': 201,
                'message': "Город не найден"
            })
    if '_ci' in request.cookies and int(request.cookies['_ci'])!=city:
        response.delete_cookie('_si', httponly=True)
        response.delete_cookie('_ri', httponly=True)
        if '_oi' in request.cookies:
            response.delete_cookie('_oi')
    response.set_cookie('_ci', str(city), expires="Tue, 19 Jan 2038 03:14:07 GMT", httponly=True, secure=True, samesite='none')
    return query


@restaurant_router.get('/getstreets', tags=['Restaurants'])
async def get_streets(request: Request):
    if '_ci' not in request.cookies:
        raise HTTPException(status_code=404, detail={
                'status': 202,
                'message': "Выберете город"
            })
    query = await Address.filter(city_id=int(request.cookies['_ci']), available=True).values('street', 'id')
    query.sort(key=lambda i : i['street'])
    return query


@restaurant_router.post('/setstreet', tags=['Restaurants'])
async def set_street(street: int, request: Request, response: Response):
    if '_ci' not in request.cookies:
        raise HTTPException(status_code=404, detail={
                'status': 202,
                'message': "Выберете город"
            })
    street_query = await Address.get_or_none(id=int(street), available=True, city_id=int(request.cookies['_ci']))
    if street_query is None:
        raise HTTPException(status_code=404, detail={
                'status': 203,
                'message': "Улица не найдена"
            })
    r = await Restaurant.get(id=street_query.restaurant_id)
    if not r.delivery: raise HTTPException(status_code=400, detail={
                'status': 207,
                'message': "Этот ресторан не доставляет на вашу улицу"
            })
    if '_ri' in request.cookies and '_oi' in request.cookies and r.id!=int(request.cookies['_ri']):
        response.delete_cookie('_oi', httponly=True, samesite='none', secure=True)
    response.set_cookie('_ri', str(r.id), expires="Tue, 19 Jan 2038 03:14:07 GMT", httponly=True, secure=True, samesite='none')
    response.set_cookie('_si', str(street), expires="Tue, 19 Jan 2038 03:14:07 GMT",  httponly=True, secure=True, samesite='none')
    return street_query

@restaurant_router.get('/paytypes', tags=['Restaurants'])
async def get_restaurant_paytypes_info(request: Request):
    if not '_ri' in request.cookies: raise HTTPException(status_code=404, detail={
                'status': 206,
                'message': "Ресторан не выбран"
            })
    if not '_si' in request.cookies: raise HTTPException(status_code=404, detail={
                'status': 204,
                'message': "Улица не выбрана"
            })
    restaurant = await Restaurant.get(id=int(request.cookies['_ri']))
    rpt_query = await RestaurantPayType.filter(restaurant_id=restaurant.id, available=True).prefetch_related('pay_type')
    rpt_list=[{'id': rpt.pay_type_id, 'name': rpt.pay_type.name} for rpt in rpt_query]
    return rpt_list


@restaurant_router.get('/', tags=['Restaurants'])
async def get_restaurant_info(request: Request, response: Response):
    if not '_ri' in request.cookies or not '_si':
        raise HTTPException(status_code=404, detail={
                'status': 206,
                'message': "Ресторан не выбран"
            })
        # restaurant = await Restaurant.get(id=2)
        # street = await Address.get(id=1)
        # response.set_cookie('_ri', 2, secure=True, samesite='none')
        # response.set_cookie('_si', 2, secure=True, samesite='none')
    else:
        restaurant = await Restaurant.get(id=int(request.cookies['_ri']))
        street = await Address.get(id=int(request.cookies['_si']))
    if not restaurant: raise HTTPException(status_code=404, detail={
                'status': 205,
                'message': "Ресторан не найден"
            })
    rpt_query = await RestaurantPayType.filter(restaurant_id=restaurant.id, available=True).prefetch_related('pay_type')
    rpt_list=[{'id': rpt.pay_type_id, 'name': rpt.pay_type.name} for rpt in rpt_query]
    return {"open": time_with_tz(restaurant.open, restaurant.timezone_IANA), "closed": time_with_tz(restaurant.closed, restaurant.timezone_IANA), "working": restaurant.working, "pay_types": rpt_list,
            "min_sum": restaurant.min_sum, "restaurant_address": restaurant.address, "client_address": street.street}