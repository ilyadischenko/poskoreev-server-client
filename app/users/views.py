import requests
from fastapi import HTTPException, APIRouter, Request, Response
from datetime import datetime, timedelta, timezone

from app.app.response import getResponseBody
from app.config import mts_token
from app.telegram.main import send_error_auth_message, send_access_call_message
from app.users.models import User, UserBlacklist
from app.users.service import validate_number
from app.users.sms import send_sms, very_complex_function_to_generate_code
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
async def confirm_code(number: str, code: str, response: Response):
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

        code = very_complex_function_to_generate_code()
        r = requests.post(url='https://api.exolve.ru/messaging/v1/SendSMS',
                          headers={
                              'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJRV05sMENiTXY1SHZSV29CVUpkWjVNQURXSFVDS0NWODRlNGMzbEQtVHA0In0.eyJleHAiOjIwMzIxOTk0NDYsImlhdCI6MTcxNjgzOTQ0NiwianRpIjoiMjNhNWMwNTYtYWQ0Yy00M2JiLWIxNzktMjBiODNjM2FjNTZmIiwiaXNzIjoiaHR0cHM6Ly9zc28uZXhvbHZlLnJ1L3JlYWxtcy9FeG9sdmUiLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoiOGUzZGNkOTQtMmE3Yy00YTU1LTlhNmQtNGFjYTJiODAxMjRjIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiYmFhOTIyMzEtYTIwNi00ZmVjLTgzZTUtOThkMzQ1NTI0NmI5Iiwic2Vzc2lvbl9zdGF0ZSI6IjljMTM3Njc0LTI1MWQtNDM1OS04ODMxLTA5YjZhYmQyNGM1OSIsImFjciI6IjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsiZGVmYXVsdC1yb2xlcy1leG9sdmUiLCJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJleG9sdmVfYXBwIHByb2ZpbGUgZW1haWwiLCJzaWQiOiI5YzEzNzY3NC0yNTFkLTQzNTktODgzMS0wOWI2YWJkMjRjNTkiLCJ1c2VyX3V1aWQiOiJmMjU5ZDgzNS1lZGNjLTRiMDQtYTZhMS0wZDBlZWUwNDY5NDEiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImNsaWVudElkIjoiYmFhOTIyMzEtYTIwNi00ZmVjLTgzZTUtOThkMzQ1NTI0NmI5IiwiY2xpZW50SG9zdCI6IjE3Mi4yMC4yLjIyIiwiYXBpX2tleSI6dHJ1ZSwiYXBpZm9uaWNhX3NpZCI6ImJhYTkyMjMxLWEyMDYtNGZlYy04M2U1LTk4ZDM0NTUyNDZiOSIsImJpbGxpbmdfbnVtYmVyIjoiMTIyMDY5NCIsImFwaWZvbmljYV90b2tlbiI6ImF1dDY3MjMzOTIxLTkyZjYtNDk5Ny04NzE2LTIzNWIwYzkwMzE4NCIsInByZWZlcnJlZF91c2VybmFtZSI6InNlcnZpY2UtYWNjb3VudC1iYWE5MjIzMS1hMjA2LTRmZWMtODNlNS05OGQzNDU1MjQ2YjkiLCJjdXN0b21lcl9pZCI6IjM2MDYzIiwiY2xpZW50QWRkcmVzcyI6IjE3Mi4yMC4yLjIyIn0.R7Q0IC0llG9Ipn9TrkQJu7Fjh2Cf5QploUZgryrMh73vJgchzJTnrXK50H85yQik7SPMRqwky8DXZrfTwOzP5PtXg6WHaOwItiuuANSLKrs4aSrctwPlRRkNcTn7rAUDPCQ-HnuP7I5kMnyY3D8htA28zqNDGjOX6b_Q20tb1FRnraQcegVLnfD-3inrxOkm9jW1n2H4A0PRBahjNyeP21Wilnm2E9ZgWlJ6Zsr76BcsOvb2e07p8kibENe5evBMK0x13RqO3gLPdwi77ht7k6IWeG5cWtaDH60OqUNGxnOt0_wmmClE1UoV5GIIAd8oVdQUVAb_IKpkh64WFZAEmA'},
                          json={
                              "number": "79249083109",
                              "destination": '7' + str(formatted_number),
                              "text": f'Ваш код - {str(code)}',
                              # "template_resource_id": 136519

                          })
        if r.status_code != 200:
            await send_error_auth_message(formatted_number, 'Произошла ошибка при авторизации')
            return getResponseBody(status=False, errorCode=106, errorMessage='Произошла какая-то ошибка. Попробуйте еще раз')

        user.expires_at = expires_at
        user.code = code
        await user.save()
        await send_access_call_message('7' + formatted_number)
    else:
        code = very_complex_function_to_generate_code()
        r = requests.post(url='https://api.exolve.ru/messaging/v1/SendSMS',
                          headers={
                              'Authorization': f'Bearer {mts_token}'},
                          json={
                              "number": "79249083109",
                              "destination": '17' + str(formatted_number),
                              "text": f'Ваш код - {str(code)}',
                              # "template_resource_id": 136519

                          })
        if r.status_code != 200:
            await send_error_auth_message(formatted_number, 'Произошла ошибка при авторизации')
            return getResponseBody(status=False, errorCode=106,
                                   errorMessage='Произошла какая-то ошибка. Попробуйте еще раз')
        await send_access_call_message('7' + formatted_number)
        await User.create(number=formatted_number, code=code, expires_at=expires_at)
# 79249083109
    print(r.json())

    return getResponseBody()
