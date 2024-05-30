from fastapi import HTTPException, APIRouter, Request, Response
from datetime import datetime, timedelta, timezone

from app.app.response import getResponseBody
from app.orders.models import Order
from app.users.models import User, UserBlacklist
from app.users.service import validate_number
# from app.users.sms import send_sms
from app.auth.jwt_handler import generateJWT, decodeJWT

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
    # active_orders = []

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
                response.delete_cookie('_at', httponly=False)
                response.delete_cookie('_oi', httponly=False)
                is_auth = False
            else:
                number = str('+7' + user.number)
                email = user.email
                telegram = user.telegram
                promocodes = await user.get_all_promocodes()
                bonuses = user.bonuses

    if '_ci' not in request.cookies:
        is_pick_city = False
    if '_ri' not in request.cookies or '_si' not in request.cookies:
        is_pick_street = False

    return getResponseBody(data={'number': number,
            'email': email,
            'telegram': telegram,
            'promocodes': promocodes,
            'bonuses': bonuses,
            'is_auth': is_auth,
            'pick_city': is_pick_city,
            'pick_street': is_pick_street,
            # 'active_orders': active_orders
            })


@user_router.post('/confirmcode', tags=['Users'])
async def confirm_code(number: str, code: str, response: Response, request: Request):
    if code == '':
        return getResponseBody(status=False, errorCode=105, errorMessage='Код не верный')
    formatted_number = await validate_number(number)
    user = await User.get(number=formatted_number)
    if datetime.now(timezone.utc) > user.expires_at:
        return getResponseBody(status=False, errorCode=104, errorMessage='Время вышло')
    if user.code != code:
        return getResponseBody(status=False, errorCode=105, errorMessage='Код не верный')
    # время токенов в utc
    access = await generateJWT(user.id)
    response.set_cookie('_at', access,
                        expires="Tue, 19 Jan 2038 03:14:07 GMT", secure=True, samesite='none')
    user.code = ''
    await user.save()

    if '_oi' in request.cookies:
        order = await Order.get(id=request.cookies['_oi'])
        order.user_id = user.id
        await order.save()

    return getResponseBody(data={'number': "+7" + user.number,
            'email': user.email,
            'telegram': user.telegram,
            'promocodes': await user.get_all_promocodes(),
            'bonuses': user.bonuses})


@user_router.post('/exit', tags=['Users'])
async def exit(response: Response):
    response.delete_cookie('_at', httponly=False, samesite='none', secure=True)
    response.delete_cookie('_oi', httponly=False, samesite='none', secure=True)
    return getResponseBody()


@user_router.post('/login', tags=['Users'])
async def send_sms_to(number: str):
    formatted_number = await validate_number(number)

    user = await User.get_or_none(number=formatted_number)

    expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=10)
    if user:
        if await UserBlacklist.filter(user_id=user.id):
            return getResponseBody(status=False, errorCode=107, errorMessage='Номер в черном списке')
        # code = await send_sms(number)
        # if not code:
        #     return getResponseBody(status=False, errorCode=106, errorMessage='Попробуйте еще раз')

        user.expires_at = expires_at
        user.code = 1234
        await user.save()
    else:
        # code = await send_sms(number)
        # if not code:
        #     return getResponseBody(status=False, errorCode=106, errorMessage='Попробуйте еще раз')

        await User.create(number=formatted_number,
                          code=1234,
                          expires_at=expires_at)
    return getResponseBody()
