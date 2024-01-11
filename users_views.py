from fastapi import HTTPException, APIRouter, Response, Request
from app.users.users_models import User, UserJWT
from app.users.sms import send_sms
from app.auth.jwt_handler import generateJWT, decodeJWT
from app.promocodes.promocodes_models import PromoCodePercent
from datetime import datetime,timedelta, timezone
from tzlocal import get_localzone
import time
user_router = APIRouter()

@user_router.get('/user')
async def get_user(request: Request, response: Response):
    access=request.cookies.get("access")
    if(not access) : raise HTTPException(status_code=401, detail="did u just delete cookie?")
    check_access = await decodeJWT(access)
    number = check_access["number"]
    if (check_access["number"] != number): raise HTTPException(status_code=401, detail="bruh")
    if(not check_access):
        #?
        #raise HTTPException(status_code=401, detail="access isnt active")
        refresh=await UserJWT.get(user_id=id)
        if(refresh.refresh_code["expires"] >= time.time()):
            refresh.is_active=False
            #обновляем рефреш
            #refresh.refresh_code=await generateJWT(number,2592000)
            #refresh.is_active=True
        if (not refresh.is_active): raise HTTPException(status_code=401, detail="refresh isnt active")
        new_access=await generateJWT(number, 3600)
        response.set_cookie("access", new_access)
    user = await User.get(phone=number)
    if (not user): raise HTTPException(status_code=404, detail=f"user with number {number} not found")
    return {'number':user.phone,
            'email':user.email,
            'telegram':user.telegram,
            'promocodes': await user.get_all_promocodes(),
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
async def confirm_code(number : str, code : str, response : Response):
    user = await User.get(phone=number)
    #конвертируем в локальную таймзону
    #if(datetime.now().astimezone()>user.time_expires.astimezone()): raise HTTPException(status_code=500, detail="TIMES UP! Better luck next time")
    #конвертируем в utc хз че лучше
    if(datetime.now(timezone.utc)>user.time_expires): raise HTTPException(status_code=500, detail="TIMES UP! Better luck next time")
    if(user.code!=code): raise HTTPException(status_code=500, detail="code is incorrect")
    #время токенов в utc
    access = await generateJWT(number, 3600)
    response.set_cookie('access', access, httponly=True,secure=True)
    refresh = await generateJWT(number, 2592000)
    await UserJWT.create(user_id=user.id,refresh_code=refresh, is_active=True)
    return {'number':user.phone,
            'email':user.email,
            'telegram':user.telegram,
            'promocodes':user.get_all_promocodes(),
            'bonuses': user.bonuses}