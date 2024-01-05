from fastapi import HTTPException, APIRouter
from promocodes_models import PromoCodePercent
promocodes_router = APIRouter()
@promocodes_router.get('/promocodes')
async def view_promocodes():
    return await PromoCodePercent.all()

@promocodes_router.post('/promocodes/add')
async def add_promocode(promocode: PromoCodePercent):
    return await PromoCodePercent.create(PromoCodePercent=promocode)

@promocodes_router.delete('/promocodes/delete/{promocode_id}')
async def delete_promocode(promocode_id : int):
    if(PromoCodePercent.filter(id=promocode_id).delete()) : return
    raise HTTPException(status_code=404, detail='promocode {promocode_id} not found')