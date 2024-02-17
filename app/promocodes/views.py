from fastapi import HTTPException, APIRouter
from app.promocodes.models import PromoCode
from app.products.models import Menu
from datetime import datetime, timezone, timedelta
from tzlocal import get_localzone

promocodes_router = APIRouter()


@promocodes_router.get('/promocodes/{id}', tags=['Promocode'])
async def view_promocode(id: int):
    promocode= await PromoCode.get_or_none(id=id)
    if not promocode: raise HTTPException(status_code=404)
    return promocode

@promocodes_router.post('/promocodes/addPromocode', tags=['Promocode'])
async def add_promocode(short_name: str, description: str, type : int, count : int, effect : float, for_all : bool,
                        start_day : datetime, end_day : datetime, min_sum : float, is_active : bool):
    return await PromoCode.create(short_name=short_name, description=description, type=type, count=count, effect=effect, for_all=for_all,
                                  start_day=start_day, end_day=end_day, min_sum=min_sum, is_active=is_active)
@promocodes_router.delete('/promocodes/delete/{promocode_id}', tags=['Promocode'])
async def delete_promocode(id: int):
    if not (await PromoCode.filter(id=id).delete()): raise HTTPException(status_code=404,
                                                                         detail=f'promocode {id} not found')
    return f"Promocode {id} deleted"

# @promocodes_router.post('/promocodes/addProduct', tags=['Promocode'])
# async def add_product(promocode_id : int, menu_id : int):
#     product = await Menu.get_or_none(id=menu_id)
#     if not product: raise HTTPException(status_code=404, detail=f'product {menu_id} not found')
#     promocode = await PromoCode.get_or_none(id=promocode_id)
#     if not promocode: raise HTTPException(status_code=404, detail=f'promocode {promocode_id} not found')
#     await promocode.works_with.add(product)
#     return promocode
#
# @promocodes_router.delete('/promocodes/removeProduct', tags=['Promocode'])
# async def remove_product(promocode_id : int, menu_id : int):
#     product = await Menu.get_or_none(id=menu_id)
#     if not product: raise HTTPException(status_code=404, detail=f'product {menu_id} not found')
#     promocode = await PromoCode.get_or_none(id=promocode_id)
#     if not promocode: raise HTTPException(status_code=404, detail=f'promocode {promocode_id} not found')
#     await promocode.works_with.remove(product)
#     return promocode

@promocodes_router.put('/promocodes/changePromocode', tags=['Promocode'])
async def change_promocode(promocode_id : int, short_name: str, description: str, type : int, count : int, effect : float, for_all : bool,
                        start_day : datetime, end_day : datetime, min_sum : float, is_active : bool):
    promocode = await PromoCode.get_or_none(id=promocode_id)
    if not promocode: raise HTTPException(status_code=404, detail=f'promocode {promocode_id} not found')
    promocode.short_name=short_name
    promocode.description=description
    promocode.type=type
    promocode.count=count
    promocode.effect=effect
    promocode.for_all=for_all,
    promocode.start_day=start_day
    promocode.end_day=end_day
    promocode.min_sum=min_sum
    promocode.is_active=is_active
    await promocode.save()
    return promocode