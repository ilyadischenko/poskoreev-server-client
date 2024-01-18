from fastapi import HTTPException, APIRouter
from app.promocodes.promocodes_models import PromoCodePercent
from datetime import datetime,timezone,timedelta
from tzlocal import get_localzone
promocodes_router = APIRouter()
@promocodes_router.get('/promocodes/{id}', tags=['Promocode'])
async def view_promocode(id : int):
    return await PromoCodePercent.get(id=id)
@promocodes_router.post('/promocodes/add', tags=['Promocode'])
async def add_promocode(short_name: str, description : str, discount : float, for_all : bool):
    start=datetime.now(tz=get_localzone())
    end=start + timedelta(days=7)
    return await PromoCodePercent.create(short_name=short_name,
    description = description,
    discount=discount,
    for_all=for_all,start=start,end=end)

@promocodes_router.delete('/promocodes/delete/{promocode_id}', tags=['Promocode'])
async def delete_promocode(id : int):
    if(not (await PromoCodePercent.filter(id=id).delete())): raise HTTPException(status_code=404, detail=f'promocode {id} not found')
    return f"Promocode {id} deleted"