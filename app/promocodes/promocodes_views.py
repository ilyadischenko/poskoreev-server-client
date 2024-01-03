from promocodes_models import PromoCode
import  datetime
async def view_promocodes():
    return await PromoCode.all()
async def add_promocode(promocode: str, name : str, expires_at : datetime):
    return await PromoCode.create(promocode=promocode, name=name, expires_at=expires_at)
async def delete_promocode(id : int):
    return await PromoCode.filter(id=id).delete()