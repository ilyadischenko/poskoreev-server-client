from fastapi import HTTPException, APIRouter, Request, Response, Depends
from tzlocal import get_localzone
from datetime import datetime, timedelta, timezone

from app.users.models import User, UserJWT, UserBlacklist
from app.users.service import AuthGuard, auth, validate_number
from app.users.sms import send_sms
from app.auth.jwt_handler import generateJWT, decodeJWT
from app.promocodes.models import PromoCode
from app.orders.views import check_active_orders
user_router = APIRouter(
    prefix='/api/v1/users'
)


@user_router.get('/', tags=['Users'])
async def get_user(
        response: Response,
        request: Request,
):
    is_pick_city = True
    is_pick_street = True
    is_auth = True

    number = ''
    email = ''
    telegram = ''
    promocodes = ''
    bonuses = ''

    # decoded_code = None
    if '_at' not in request.cookies:
        is_auth = False
    else:
        decoded_code = await decodeJWT(request.cookies.get('_at'))
        if not decoded_code:
            is_auth = False
        else:
            user = await User.get_or_none(id=decoded_code['id'])
            if not user:
                response.delete_cookie('_at', httponly=False, samesite='none', secure=True)
                response.delete_cookie('_oi', httponly=False, samesite='none', secure=True)
                is_auth = False
            else:
                number = str('8' + user.number)
                email = user.email
                telegram = user.telegram
                promocodes = await user.get_all_promocodes()
                bonuses = user.bonuses


    if '_ci' not in request.cookies:
        is_pick_city = False
    if '_ri' not in request.cookies or '_si' not in request.cookies:
        is_pick_street = False



    return {'number': number,
            'email': email,
            'telegram': telegram,
            'promocodes': promocodes,
            'bonuses': bonuses,
            'is_auth': is_auth,
            'pick_city': is_pick_city,
            'pick_street': is_pick_street,
            'active_orders': await check_active_orders(decoded_code['id'])
            }


@user_router.post('/confirmcode', tags=['Users'])
async def confirm_code(number: str, code: str, response: Response):
    formatted_number = await validate_number(number)
    user = await User.get(number=formatted_number)
    if datetime.now(timezone.utc) > user.expires_at: raise HTTPException(status_code=408,
                                                                         detail="Время вышло")
    if user.code != code: raise HTTPException(status_code=401, detail="code is incorrect")
    # время токенов в utc
    access = await generateJWT(user.id)
    response.set_cookie('_at', access, httponly=False, samesite='none', secure=True)
    return {'number': "8" + user.number,
            'email': user.email,
            'telegram': user.telegram,
            'promocodes': await user.get_all_promocodes(),
            'bonuses': user.bonuses}


@user_router.post('/exit', tags=['Users'])
async def exit(response: Response):
    response.delete_cookie('_at', httponly=False, samesite='none', secure=True)
    response.delete_cookie('_oi', httponly=False, samesite='none', secure=True)
    return 'ok'


@user_router.post('/login', tags=['Users'])
async def send_sms_to(number: str):
    formatted_number = await validate_number(number)
    user = await User.get_or_none(number=formatted_number)
    code = await send_sms()
    expires_at = datetime.now(tz=get_localzone()) + timedelta(minutes=10)
    if (not code): raise HTTPException(status_code=500, detail="apparently code wasnt generated")
    if user:
        if await UserBlacklist.filter(user_id=user.id): raise HTTPException(status_code=403,
                                                                            detail=f" {number} is in blacklist")
        user.expires_at = expires_at
        user.code = code
        await user.save()
    else:
        await User.create(number=formatted_number, code=code, expires_at=expires_at)
    return f"code was sent to {number} and will expire at {expires_at}"

# @user_router.post('/dev/promocodes/give', tags=['dev'])
# async def give_promocode(number: str, promocode_id: int):
#     formatted_number = await validate_number(number)
#     user = await User.get(number=formatted_number)
#     if not user: raise HTTPException(status_code=404, detail=f"user with number {number} not found")
#     promocode = await PromoCode.get(id=promocode_id)
#     if not promocode: raise HTTPException(status_code=404, detail=f"promocode with id {promocode_id} not found")
#     await user.promocodes.add(promocode)
#     return f"promocode with id {promocode_id} was given to user {number}"
#
#
# @user_router.delete('/dev/promocodes/remove', tags=['dev'])
# async def remove_promocode(number: str, promocode_id: int):
#     user = await User.get(number=number)
#     if not user: raise HTTPException(status_code=404, detail=f"user with number {number} not found")
#     promocode = await PromoCode.get(id=promocode_id)
#     if not promocode: raise HTTPException(status_code=404, detail=f"promocode with id {promocode_id} not found")
#     await user.promocodes.remove(promocode)
#     return f"promocode with id {promocode_id} removed from user {number}"