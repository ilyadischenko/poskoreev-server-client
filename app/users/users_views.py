from fastapi import HTTPException, APIRouter, Response, Request
from tzlocal import get_localzone
import time
from datetime import datetime, timedelta, timezone

from app.users.users_models import User, UserJWT, UserBlacklist
from app.users.sms import send_sms
from app.auth.jwt_handler import generateJWT, decodeJWT
from app.promocodes.promocodes_models import PromoCodePercent
from app.users.users_requests_models import RefreshModels

user_router = APIRouter()


# @user_router.post('/api/v1/refresh', tags=['Users'])
# async def refresh_token(data: RefreshModels, response: Response):
#     if not await UserJWT.get(refresh_code=data.refresh, is_active=True).exists():
#         raise HTTPException(status_code=401, detail='refresh isnt active')
#
#     decoded_refresh = await decodeJWT(data.refresh)
#     user_id = decoded_refresh['id']
#     expires = decoded_refresh['expires']
#
#     if expires <= time.time(): raise HTTPException(status_code=401, detail='refresh isnt active')
#
#     await UserJWT.get(refresh_code=data.refresh, is_active=True).update(is_active=False)
#
#     new_refresh = await generateJWT(user_id, 2592000)
#     await UserJWT.create(user_id=user_id, refresh_code=new_refresh, is_active=True)
#
#     new_access = await generateJWT(user_id, 3600)
#     response.set_cookie('access', new_access)
#     return {
#         'refresh': new_refresh
#     }


@user_router.get('/api/v1/getuserinfo', tags=['Users'])
async def get_user(request: Request):
    print('-------------------------------')
    print(request.cookies)
    print('-------------------------------')
    access = request.cookies.get("access")
    if not access: raise HTTPException(status_code=401, detail="did u just delete cookie?")

    check_access = await decodeJWT(access)
    if not check_access: raise HTTPException(status_code=401, detail="access isnt active")
    user_id = check_access["id"]
    user = await User.get(id=user_id)
    if not user: raise HTTPException(status_code=404, detail=f"user with number {user_id} not found")
    return {'number': user.number,
            'email': user.email,
            'telegram': user.telegram,
            'promocodes': await user.get_all_promocodes(),
            'bonuses': user.bonuses}


@user_router.post('/api/v1/confirmcode', tags=['Users'])
async def confirm_code(number: str, code: str, response: Response):
    user = await User.get(number=number)
    if datetime.now(timezone.utc) > user.expires_at: raise HTTPException(status_code=500,
                                                                         detail="TIMES UP! Better luck next time")
    if user.code != code: raise HTTPException(status_code=401, detail="code is incorrect")
    # время токенов в utc
    access = await generateJWT(user.id, 3600)
    response.set_cookie('access', access, httponly=False, samesite='none', secure=True)
    refresh = await generateJWT(user.id, 2592000)
    await UserJWT.create(user_id=user.id, refresh_code=refresh, is_active=True)
    return {'number': user.number,
            'email': user.email,
            'telegram': user.telegram,
            'promocodes': await user.get_all_promocodes(),
            'bonuses': user.bonuses,
            'refresh': refresh
            }

@user_router.post('/api/v1/exit', tags=['Users'])
async def exit(response: Response):
    response.delete_cookie('access', httponly=False, samesite='none', secure=True)
    return 'ok'


@user_router.post('/api/v1/login', tags=['Users'])
async def send_sms_to(number: str):
    code = await send_sms()
    if (not code): raise HTTPException(status_code=500, detail="apparently code wasnt generated")
    # в базе будет хранится локальное время с таймзоной но вернется в utc почему хз
    expires_at = datetime.now(tz=get_localzone()) + timedelta(minutes=10)
    user = await User.get_or_none(number=number)
    if user:
        if (await UserBlacklist.filter(user_id=user.id)): raise HTTPException(status_code=403, detail=f" {number} is in blacklist")
        user.expires_at=expires_at
        user.code=code
    else:
        await User.create(number=number, code=code, expires_at=expires_at)
    return f"code was sent to {number} and will expire at {expires_at}"


@user_router.post('/dev/promocodes/give', tags=['dev'])
async def give_promocode(number: str, promocode_id: int):
    user = await User.get(number=number)
    if not user: raise HTTPException(status_code=404, detail=f"user with number {number} not found")
    promocode = await PromoCodePercent.get(id=promocode_id)
    if not promocode: raise HTTPException(status_code=404, detail=f"promocode with id {promocode_id} not found")
    await user.promocodes.add(promocode)
    return f"promocode with id {promocode_id} was given to user {number}"


@user_router.delete('/dev/promocodes/remove', tags=['dev'])
async def remove_promocode(number: str, promocode_id: int):
    user = await User.get(number=number)
    if not user: raise HTTPException(status_code=404, detail=f"user with number {number} not found")
    promocode = await PromoCodePercent.get(id=promocode_id)
    if not promocode: raise HTTPException(status_code=404, detail=f"promocode with id {promocode_id} not found")
    await user.promocodes.remove(promocode)
    return f"promocode with id {promocode_id} removed from user {number}"


@user_router.delete('/dev/deleteUser', tags=['dev'])
async def delete_user(number: str):
    if not (await User.filter(number=number).delete()): raise HTTPException(status_code=404,
                                                                            detail=f"user {number} not found")
    return f"user {number} deleted"

@user_router.post('/dev/banUser', tags=['dev'])
async def banUser(id : int):
    if not (await UserBlacklist.create(user_id=id)): raise HTTPException(status_code=400, detail="oops something went wrong")
    return f"user {id} banned"
@user_router.delete('/dev/unbanUser', tags=['dev'])
async def unbanUser(id : int):
    if not (await UserBlacklist.filter(user_id=id).delete()): raise HTTPException(status_code=400, detail="oops something went wrong")
    return f"user {id} unbanned"