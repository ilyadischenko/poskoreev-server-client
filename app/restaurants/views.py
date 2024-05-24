import requests
from fastapi import HTTPException, APIRouter, Request, Response, Depends
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

from app.app.jwtService import generateJWT, decodeJWT
from app.app.response import getResponseBody, setResponseCookie
from app.config import yandex_api_key
from app.restaurants.models import Restaurant, City, RestaurantPayType, DeliveryZones
from app.restaurants.schemas import SetAdressSchema
from app.restaurants.service import (time_with_tz, CookieCheckerRestaurant, CCR, CookieCheckerCity, CCC,
                                     CookieCheckerAddress, CCA)

restaurant_router = APIRouter(
    prefix="/api/v1/restaurants"
)


@restaurant_router.get('/getCities', tags=['Restaurants'])
async def get_cities():
    # add sort
    query = await City.all().values('id', 'name')
    query.sort(key=lambda i: i['name'])
    return query


@restaurant_router.post('/setcity', tags=['Restaurants'])
async def set_city(city: int, request: Request, response: Response):
    # если удалить город из кук, то ресторан, улица и заказ не удалятся
    # проверить на наличие рестика
    query = await City.get_or_none(id=city)
    if query is None: raise HTTPException(status_code=404, detail={
        'status': 201,
        'message': "Город не найден"
    })
    if query.id != city:
        response.delete_cookie('_si', httponly=True)
        response.delete_cookie('_ri', httponly=True)
        if '_oi' in request.cookies:
            response.delete_cookie('_oi')
    response.set_cookie('_ci', str(city), expires="Tue, 19 Jan 2038 03:14:07 GMT", httponly=True, secure=True,
                        samesite='none')
    return query


@restaurant_router.get('/findaddres', tags=['Restaurants'])
async def find_addres(
        query: str,
        city_id: CookieCheckerCity = Depends(CCC),
        # user_id: AuthGuard = Depends(auth),
):
    """Роут возвращает список улиц, которые отдает яндекс геокодер"""

    city = await City.get_or_none(id=city_id)
    r = requests.get(
        url=f'https://geocode-maps.yandex.ru/1.x/?apikey={yandex_api_key}&geocode={city.name}, {query}&results=12&format=json')

    if not r.json()['response']['GeoObjectCollection']['featureMember']:
        return getResponseBody(data={'addresses': []})

    addressList = []
    for i in r.json()['response']['GeoObjectCollection']['featureMember']:
        if (i['GeoObject']['metaDataProperty']['GeocoderMetaData']['kind'] == 'house'
                or i['GeoObject']['metaDataProperty']['GeocoderMetaData']['kind'] == 'entrance'
                or i['GeoObject']['metaDataProperty']['GeocoderMetaData']['kind'] == 'street'
        ):
            addressList.append({
                'name': i['GeoObject']['name'],
                'description': i['GeoObject']['description'],
                'formattedAddress': i['GeoObject']['metaDataProperty']['GeocoderMetaData']['text'],
                'position': i['GeoObject']['Point']['pos'],
                'kind': i['GeoObject']['metaDataProperty']['GeocoderMetaData']['kind']
            })

    return getResponseBody(
        data={'addresses': addressList, 'r': r.json()['response']['GeoObjectCollection']['featureMember']})


@restaurant_router.get('/viewJWT', tags=['Restaurants'])
async def viewJWT(request: Request):
    cookie = request.cookies['_picked_address']
    return decodeJWT(cookie)


@restaurant_router.post('/setaddress', tags=['Restaurants'])
async def setAddress(
        data: SetAdressSchema,
        response: Response,
        city_id: CookieCheckerCity = Depends(CCC),
):
    """Роут принимает долготу и широты, проверяет доставляем ли мы туда и зашивает куки адреса с данными"""
    if data.kind == 'street':
        return getResponseBody(status=False, errorCode=217, errorMessage='Укажите адрес с домом')

    zones = await DeliveryZones.filter(city_id=city_id, is_active=True).values('coordinates', 'restaurant_id', 'name', 'id')
    if not zones:
        return getResponseBody(status=False, errorCode=215, errorMessage='Пожалуйста, выберите другой город')
    allowed_coordinates = []

    for i in zones:
        print(i)
        allowed_coordinates.append({
            'zoneName': i['name'],
            'zoneId': i['id'],
            'coordinates': i['coordinates']['coordinates'],
            'restaurant': i['restaurant_id']
        })

    position = data.position.split(' ')
    longitude = float(position[0])
    latitude = float(position[1])
    point = Point(longitude, latitude)

    for e in allowed_coordinates:
        polygon = Polygon(e['coordinates'])
        flag = polygon.contains(point)
        if flag:
            setResponseCookie(response, name='_ri', data=e['restaurant'])
            setResponseCookie(response, name='_delivery_zone', data=e['zoneId'])
            setResponseCookie(response, name='_picked_address', data=generateJWT({
                'restaurant_id': e['restaurant'],
                'city_id': city_id,
                'description': data.description,
                'formattedAddress': data.formattedAddress,
                'address': data.address,
                'longitude': longitude,
                'latitude': latitude,
                'zone_id': e['zoneId'],
                'zone_name': e['zoneName']
                # 'entrance': data.entrance,
                # 'floor': data.floor,
                # 'apartment': data.apartment,
                # 'comment': data.comment,
            }))
            return getResponseBody(status=True)

    return getResponseBody(status=False, errorCode=216, errorMessage='К сожалению, мы сюда не доставляем :(')


# @restaurant_router.get('/getstreets', tags=['Restaurants'])
# async def get_streets(city_id: CookieCheckerCity = Depends(CCC)):
#     query = await Address.filter(city_id=city_id, available=True).values('street', 'id')
#     query.sort(key=lambda i: i['street'])
#     return query


# @restaurant_router.post('/setstreet', tags=['Restaurants'])
# async def set_street(street: int, request: Request, response: Response, city_id: CookieCheckerCity = Depends(CCC)):
#     if (('_ri' not in request.cookies and '_si' in request.cookies and int(request.cookies['_si']) != street)
#             or ('_ri' not in request.cookies and '_si' not in request.cookies)):
#         response.delete_cookie('_oi', httponly=True, samesite='none', secure=True)
#     street_query = await Address.get_or_none(id=int(street), available=True, city_id=city_id)
#     if street_query is None:
#         raise HTTPException(status_code=404, detail={
#             'status': 203,
#             'message': "Улица не найдена"
#         })
#     r = await Restaurant.get(id=street_query.restaurant_id)
#     if not r.delivery: raise HTTPException(status_code=400, detail={
#         'status': 207,
#         'message': "Этот ресторан не доставляет на вашу улицу"
#     })
#     if '_ri' in request.cookies and '_oi' in request.cookies and r.id != int(request.cookies['_ri']):
#         response.delete_cookie('_oi', httponly=True, samesite='none', secure=True)
#     response.set_cookie('_ri', str(r.id), expires="Tue, 19 Jan 2038 03:14:07 GMT", httponly=True, secure=True,
#                         samesite='none')
#     response.set_cookie('_si', str(street), expires="Tue, 19 Jan 2038 03:14:07 GMT", httponly=True, secure=True,
#                         samesite='none')
#     return street_query


@restaurant_router.get('/paytypes', tags=['Restaurants'])
async def get_restaurant_paytypes_info(restaurant_id: CookieCheckerRestaurant = Depends(CCR)):
    restaurant = await Restaurant.get(id=restaurant_id)
    rpt_query = await RestaurantPayType.filter(restaurant_id=restaurant.id, available=True).prefetch_related('pay_type')
    rpt_list = [{'id': rpt.pay_type_id, 'name': rpt.pay_type.name} for rpt in rpt_query]
    return rpt_list


@restaurant_router.get('/', tags=['Restaurants'])
async def get_restaurant_info(restaurant_id: CookieCheckerRestaurant = Depends(CCR),
                              address: CookieCheckerAddress = Depends(CCA)
                              ):
    restaurant = await Restaurant.get(id=restaurant_id)
    if not restaurant: raise HTTPException(status_code=404, detail={
        'status': 205,
        'message': "Ресторан не найден"
    })
    rpt_query = await RestaurantPayType.filter(restaurant_id=restaurant.id, available=True).prefetch_related('pay_type')
    rpt_list = [{'id': rpt.pay_type_id, 'name': rpt.pay_type.name} for rpt in rpt_query]
    return {"open": time_with_tz(restaurant.open, restaurant.timezone_IANA),
            "closed": time_with_tz(restaurant.closed, restaurant.timezone_IANA), "working": restaurant.working,
            "pay_types": rpt_list,
            "min_sum": restaurant.min_sum, "restaurant_address": restaurant.address, "client_address": address['address']}
