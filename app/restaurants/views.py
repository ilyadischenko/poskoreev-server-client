import datetime

from fastapi import HTTPException, APIRouter
from app.restaurants.models import Restaurant, Address
restaurant_router = APIRouter()
@restaurant_router.post('/addRestaurant', tags=['Restaurants'])
async def add_restaurant(open : datetime.time, closed : datetime.time, address : str, delivery : bool, pickup : bool, inside: bool,
                   working : bool, city : str, min_sum: int):
    return await Restaurant.create(open=open, closed=closed, address=address, delivery=delivery, pickup=pickup, inside=inside,
                            working=working, city=city, min_sum=min_sum)
@restaurant_router.put('/updateRestaurant', tags=['Restaurants'])
async def update_restaurant(id : int, open : datetime.time, closed : datetime.time, address : str, delivery : bool, pickup : bool, inside: bool,
                   working : bool, city : str, min_sum: int):
    return await Restaurant.filter(id=id).update(open=open, closed=closed, address=address, delivery=delivery, pickup=pickup, inside=inside,
                                                 working=working, city=city, min_sum=min_sum)

@restaurant_router.delete('/deleteRestaurant', tags=['Restaurants'])
async def delete_restaurant(id : int):
    return await Restaurant.filter(id=id).delete()
@restaurant_router.post('/addAddress', tags=['Restaurants'])
async def add_address(restaurant_id: int, street):
    return await Address.create(restaurant_id=restaurant_id, street=street)
@restaurant_router.delete('/deleteAddress', tags=['Restaurants'])
async def delete_address(id : int):
    return await Address.filter(id=id).delete()
@restaurant_router.put('/updateAddress', tags=['Restaurants'])
async def update_address(id : int, street : str, available : bool):
    return await Address.filter(id=id).update(street=street, available=available)
@restaurant_router.put('/changeAddressAssignment', tags=['Restaurants'])
async def change_address_assignment(id : int, restaurant_id: int):
    return await Address.filter(id=id).update(restaurant_id=restaurant_id)