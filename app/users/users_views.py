from fastapi import HTTPException, APIRouter
from app.users.users_models import User
from app.users.sms import send_sms
from app.auth.jwt_handler import generateJWT
from app.promocodes.promocodes_models import PromoCodePercent
from datetime import datetime,timezone,timedelta
from tzlocal import get_localzone
user_router = APIRouter()

@user_router.get('/{number}')
async def get_user(number : str):
    user=await User.get(phone=number)
    if(not user): raise HTTPException(status_code=404, detail=f"user with number {number} not found")
    return user

@user_router.post('/promocodes/give')
async def give_promocode(number : str, promocode_id : int):
    user=await User.get(phone=number)
    if(not user): raise HTTPException(status_code=404, detail=f"user with number {number} not found")
    promocode = await PromoCodePercent.get(id=promocode_id)
    if(not promocode): raise HTTPException(status_code=404, detail=f"promocode with id {promocode_id} not found")
    await user.promocodes.add(promocode)
    return f"promocode with id {promocode_id} was given to user {number}"

@user_router.delete('/promocodes/remove')
async def remove_promocode(number : str, promocode_id : int):
    user=await User.get(phone=number)
    if(not user): raise HTTPException(status_code=404, detail=f"user with number {number} not found")
    promocode = await PromoCodePercent.get(id=promocode_id)
    if(not promocode): raise HTTPException(status_code=404, detail=f"promocode with id {promocode_id} not found")
    await user.promocodes.remove(promocode)
    return f"promocode with id {promocode_id} removed from user {number}"

@user_router.post('/login')
async def send_sms_to(number : str):
    code = await send_sms()
    if(not code): raise HTTPException(status_code=500,detail="apparently code wasnt generated")
    #в базе будет хранится локальное время с таймзоной но вернется в utc почему хз
    time_expires = datetime.now(tz=get_localzone()) + timedelta(minutes=10)
    return await User.create(phone=number,code=code,time_expires=time_expires)

@user_router.delete('/delete')
async def delete_user(number: str):
    if (not (await User.filter(phone=number).delete())): raise HTTPException(status_code=404, detail=f"user {number} not found")
    return f"user {number} deleted"

@user_router.post('/cofirm')
async def confirm_code(number : str, code : str):
    user = await User.get(phone=number)
    #сравниваем тоже в utc
    if(datetime.now(timezone.utc)>user.time_expires):
        await delete_user(number)
        raise HTTPException(status_code=500, detail="TIMES UP! Better luck next time")
    if(user.code!=code): raise HTTPException(status_code=500, detail="code is incorrect")
    access = await generateJWT(number, 3600)
    refresh = await generateJWT(number, 2592000)
    #promocodes=await PromoCodePercent.filter(for_all=True)
    # for promocode in promocodes:
    #     user.promocodes.add(promocode)
    return {'number':user.phone,
            'email':user.email,
            'telegram':user.telegram,
            'bonuses':user.bonuses,
            #'promocodes':user.promocodes,
            'access':access,
            'refresh':refresh}