import time
import jwt
from decouple import config
from app.users.users_models import UserJWT
from fastapi import Response, Request, HTTPException
jwt_secret=config('secret')
jwt_algorithm=config('algorithm')
async def generateJWT(id: int, time_token_seconds : int):
    payload = {
        "id": id,
        "expires": time.time() + time_token_seconds
    }
    token = jwt.encode(payload, jwt_secret, algorithm=jwt_algorithm)
    return token

async def decodeJWT(token: str):
    decoded_token = jwt.decode(token, jwt_secret, algorithms=[jwt_algorithm])
    return decoded_token if decoded_token["expires"] >= time.time() else None

# async def checkJWT(id : int, response: Response, request: Request):
#     access=request.cookies.get("access")
#     check_access = await decodeJWT(access)
#     number = check_access["number"]
#     if (check_access["number"] != number): raise HTTPException(status_code=401, detail="bruh")
#     if(not check_access):
#         refresh=await UserJWT.get(user_id_id=id)
#         if(refresh.refresh_code["expires"] >= time.time()): refresh.is_active=False
#         if (not refresh.is_active): raise HTTPException(status_code=401, detail="refresh isnt active")
#         new_access=await generateJWT(number, 3600)
#         response.set_cookie("access", new_access)