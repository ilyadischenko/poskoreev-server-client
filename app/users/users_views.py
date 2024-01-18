from fastapi import HTTPException, APIRouter, Response, Request
from tzlocal import get_localzone
import time
from datetime import datetime, timedelta, timezone

from app.users.users_models import User, UserJWT
from app.users.sms import send_sms
from app.auth.jwt_handler import generateJWT, decodeJWT
from app.promocodes.promocodes_models import PromoCodePercent

user_router = APIRouter()


@user_router.post('/api/v1/refresh', tags=['Users'])
async def refresh_token(number: str, id: int, response: Response):
    refresh = await UserJWT.get(user_id=id)
    if (refresh.refresh_code["expires"] >= time.time()):
        refresh.is_active = False
        refresh.refresh_code = await generateJWT(number, 2592000)
        refresh.is_active = True
    if (not refresh.is_active): raise HTTPException(status_code=401, detail="refresh isnt active")
    new_access = await generateJWT(number, 3600)
    response.set_cookie("access", new_access)


@user_router.get('/api/v1/getuserinfo', tags=['Users'])
async def get_user(request: Request):
    access = request.cookies.get("access")
    if (not access): raise HTTPException(status_code=401, detail="did u just delete cookie?")
    check_access = await decodeJWT(access)
    number = check_access["number"]
    if (check_access["number"] != number): raise HTTPException(status_code=401, detail="bruh")
    if (not check_access): raise HTTPException(status_code=401, detail="access isnt active")
    user = await User.get(number=number)
    if (not user): raise HTTPException(status_code=404, detail=f"user with number {number} not found")
    return {'number': user.number,
            'email': user.email,
            'telegram': user.telegram,
            'promocodes': await user.get_all_promocodes(),
            'bonuses': user.bonuses}


@user_router.post('/api/v1/cofirmcode', tags=['Users'])
async def confirm_code(number: str, code: str, response: Response):
    user = await User.get(number=number)
    if datetime.now(timezone.utc) > user.expires_at: raise HTTPException(status_code=500,
                                                                         detail="TIMES UP! Better luck next time")
    if user.code != code: raise HTTPException(status_code=401, detail="code is incorrect")
    # время токенов в utc
    access = await generateJWT(number, 3600)
    response.set_cookie('access', access, httponly=True, secure=True)
    refresh = await generateJWT(number, 2592000)
    await UserJWT.create(user_id=user.id, refresh_code=refresh, is_active=True)
    return {'number': user.number,
            'email': user.email,
            'telegram': user.telegram,
            'promocodes': await user.get_all_promocodes(user.id),
            'bonuses': user.bonuses}


@user_router.post('/api/v1/login', tags=['Users'])
async def send_sms_to(number: str):
    code = await send_sms()
    if (not code): raise HTTPException(status_code=500, detail="apparently code wasnt generated")
    # в базе будет хранится локальное время с таймзоной но вернется в utc почему хз
    expires_at = datetime.now(tz=get_localzone()) + timedelta(minutes=10)
    if await User.filter(number=number).exists():
        await User.filter(number=number).update(expires_at=expires_at, code=code)
    else:
        await User.update_or_create(number=number, code=code, expires_at=expires_at)
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
