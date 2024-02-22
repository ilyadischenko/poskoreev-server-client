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


@restaurant_router.post('/addRestaurant', tags=['Restaurants dev'])
async def add_restaurant(open: datetime.time, closed: datetime.time, address: str, delivery: bool, pickup: bool,
                         inside: bool,
                         working: bool, city: str, min_sum: int):
    return await Restaurant.create(open=open, closed=closed, address=address, delivery=delivery, pickup=pickup,
                                   inside=inside,
                                   working=working, city=city, min_sum=min_sum)


@restaurant_router.put('/updateRestaurant', tags=['Restaurants dev'])
async def update_restaurant(id: int, open: datetime.time, closed: datetime.time, address: str, delivery: bool,
                            pickup: bool, inside: bool,
                            working: bool, city: str, min_sum: int):
    return await Restaurant.filter(id=id).update(open=open, closed=closed, address=address, delivery=delivery,
                                                 pickup=pickup, inside=inside,
                                                 working=working, city=city, min_sum=min_sum)


@restaurant_router.delete('/deleteRestaurant', tags=['Restaurants dev'])
async def delete_restaurant(id: int):
    return await Restaurant.filter(id=id).delete()


@restaurant_router.post('/addAddress', tags=['Restaurants dev'])
async def add_address(restaurant_id: int, street):
    return await Address.create(restaurant_id=restaurant_id, street=street)


@restaurant_router.delete('/deleteAddress', tags=['Restaurants dev'])
async def delete_address(id: int):
    return await Address.filter(id=id).delete()


@restaurant_router.put('/updateAddress', tags=['Restaurants dev'])
async def update_address(id: int, street: str, available: bool):
    return await Address.filter(id=id).update(street=street, available=available)


@restaurant_router.put('/changeAddressAssignment', tags=['Restaurants dev'])
async def change_address_assignment(id: int, restaurant_id: int):
    return await Address.filter(id=id).update(restaurant_id=restaurant_id)
