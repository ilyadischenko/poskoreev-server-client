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
    if(user): return user
    raise HTTPException(status_code=404, detail=f"user with number {number} not found")

@user_router.post('/promocodes/give')
async def give_promocode(number : str, promocode_id : int):
    user=await User.get(phone=number)
    promocode = await PromoCodePercent.get(id=promocode_id)
    if(user): return await user.promocodes.add(promocode)
    raise HTTPException(status_code=404, detail=f"user with number {number} not found")

@user_router.delete('/promocodes/remove')
async def remove_promocode(number : str, promocode_id : int):
    user=await User.get(phone=number)
    if(user): return await user.promocodes.remove(id=promocode_id)
    raise HTTPException(status_code=404, detail=f"user with number {number} not found")

@user_router.post('/login')
async def send_sms_to(number : str):
    code = await send_sms()
    if(code):
        #в базе будет хранится локальное время с таймзоной но вернется в utc почему хз
        time_expires = datetime.now(tz=get_localzone()) + timedelta(minutes=10)
        return await User.create(phone=number,code=code,time_expires=time_expires)
    raise HTTPException(status_code=500,detail="apparently code wasnt generated")

@user_router.post('/cofirm')
async def confirm_code(number : str, code : str):
    user = await User.get(phone=number)
    #сравниваем тоже в utc
    if(user.code==code and datetime.now(timezone.utc)<user.time_expires):
        access = await generateJWT(number, 3600)
        refresh = await generateJWT(number, 2592000)
        promocodes=await PromoCodePercent.filter(for_all=True)
        for promocode in promocodes:
            user.promocodes.add(promocode)
        return {'number':user.phone,
                'email':user.email,
                'telegram':user.telegram,
                'bonuses':user.bonuses,
                'promocodes':user.promocodes,
                'access':access,
                'refresh':refresh}
    raise HTTPException(status_code=500,detail="someone messed up")