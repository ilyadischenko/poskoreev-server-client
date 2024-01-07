from fastapi import HTTPException, APIRouter
from app.users.users_models import User, UserJWT
from app.users.sms import send_sms
from app.auth.jwt_handler import generateJWT
from app.promocodes.promocodes_models import PromoCodePercent
from datetime import datetime,timedelta
from tzlocal import get_localzone
user_router = APIRouter()

@user_router.get('/{number}')
async def get_user(number : str):
    user=await User.get(phone=number)
    promocodes_set=await user.promocodes.all()
    promocodes=[]
    for i in promocodes_set:
        promocodes.append({'promocode' :i.short_name, 'discount': i.discount, 'expires at' : i.end.astimezone()})
    if(not user): raise HTTPException(status_code=404, detail=f"user with number {number} not found")
    return {'number':user.phone,
            'email':user.email,
            'telegram':user.telegram,
            'promocodes': promocodes,
            'bonuses': user.bonuses}

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
    await User.create(phone=number,code=code,time_expires=time_expires)
    return f"code was sent to {number} and will expire at {time_expires}"

@user_router.delete('/delete')
async def delete_user(number: str):
    if (not (await User.filter(phone=number).delete())): raise HTTPException(status_code=404, detail=f"user {number} not found")
    return f"user {number} deleted"

@user_router.post('/cofirm')
async def confirm_code(number : str, code : str):
    user = await User.get(phone=number)
    #конвертируем в локальную таймзону
    if(datetime.now().astimezone()>user.time_expires.astimezone()): raise HTTPException(status_code=500, detail="TIMES UP! Better luck next time")
    #конвертируем в utc хз че лучше
    #if(datetime.now(timezone.utc)>user.time_expires): raise HTTPException(status_code=500, detail="TIMES UP! Better luck next time")
    if(user.code!=code): raise HTTPException(status_code=500, detail="code is incorrect")
    #время токенов в utc
    #access = await generateJWT(number, 3600)
    refresh = await generateJWT(number, 2592000)
    await UserJWT.create(id_id=user.id,refresh_code=refresh) #<-debil
    promocodes_set=await user.promocodes.all()
    promocodes=[]
    for i in promocodes_set:
        promocodes.append({'promocode' :i.short_name, 'discount': i.discount, 'expires at' : i.end.astimezone()})
    return {'number':user.phone,
            'email':user.email,
            'telegram':user.telegram,
            'promocodes':promocodes,
            'bonuses': user.bonuses}