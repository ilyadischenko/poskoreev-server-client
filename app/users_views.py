import time

from fastapi import HTTPException, APIRouter
from users_models import User
from sms import send_sms,confirm_sms
from app.auth.jwt_handler import generateJWT
import datetime

router = APIRouter()
@router.get('/{number}')
async def get_user(number : str):
    user=await User.get(number=number)
    if(user): return user
    raise HTTPException(status_code=404, detail=f"user with number {number} not found")

@router.post('/login')
async def send_sms(number : str):
    result = await send_sms(number)
    if(result): #update sms func
        current_time = datetime.datetime.now() + datetime.timedelta(minutes=10)
        await User.update_or_create(number=number,code=result,time_expires=current_time)
        return #HTTPException(status_code=200)
    raise HTTPException(status_code=404)
@router.post('/cofirm')
async def confirm_code(number : str, code : int):
    user = await User.get(number=number)
    if(user.code==code and user.time_expires>datetime.datetime.now()):
        access = await generateJWT(number, 3600)
        refresh = await generateJWT(number, 2592000)
        #promocodes = await User.promocodes
        return {'number' : user.phone,
               'email' : user.email,
               'telegram' : user.telegram,
               'bonuses' : user.bonuses,
                'access' : access,
                'refresh' : refresh}
async def write_code(number : str, code: int):
    current_time = datetime.datetime.now() + datetime.timedelta(minutes=10)
    user = User.filter(number=number)
    if(user): return await user.update(code=code, time_expires=current_time)
    raise HTTPException(status_code=404, detail=f"User with number {number} not found")

async def get_code(number: str):
    user = await User.get(number=number)
    if(user): return {'code': user.code, 'time_expires': user.time_expires}
    raise HTTPException(status_code=404, detail=f"User with number {number} not found")