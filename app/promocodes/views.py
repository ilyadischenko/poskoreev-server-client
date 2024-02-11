from fastapi import HTTPException, APIRouter
from app.promocodes.models import PromoCode, PromoCodeModel, PromoCodeType
from datetime import datetime, timezone, timedelta
from tzlocal import get_localzone

promocodes_router = APIRouter()


@promocodes_router.get('/promocodes/{id}', tags=['Promocode'])
async def view_promocode(id: int):
    return await PromoCode.get(id=id)


@promocodes_router.post('/promocodes/addPromocodeModel', tags=['Promocode'])
async def add_promocode_model(short_name: str, description: str):
    return await PromoCodeModel.create(short_name=short_name, description=description)

@promocodes_router.post('/promocodes/addPromocodeType', tags=['Promocode'])
async def add_promocode_type(type: str):
    return await PromoCodeType.create(type=type)

@promocodes_router.post('/promocodes/addPromocode', tags=['Promocode'])
async def add_promocode(promocode_id : int, type_id: int, discount : float, for_all : bool,
                        start_day : datetime, end_day : datetime, min_sum : float, is_active : bool):
    return await PromoCode.create(promocode_id=promocode_id, type_id=type_id, discount=discount, for_all=for_all,
                                  start_day=start_day, end_day=end_day, min_sum=min_sum, is_active=is_active)
@promocodes_router.delete('/promocodes/delete/{promocode_id}', tags=['Promocode'])
async def delete_promocode(id: int):
    if (not (await PromoCode.filter(id=id).delete())): raise HTTPException(status_code=404,
                                                                                  detail=f'promocode {id} not found')
    return f"Promocode {id} deleted"